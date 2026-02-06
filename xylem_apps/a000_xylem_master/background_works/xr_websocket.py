import os, asyncio, websockets, json, time, logging, threading, datetime, queue, base64, traceback, copy
from os import urandom
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

from xylem_apps.a000_xylem_master import serve

xr_handler_logger = logging.getLogger(serve.xylem_remote_handler_log_name)
handshake_completed = asyncio.Event()

# Generate Key Pair
private_key = rsa.generate_private_key(
    public_exponent = 65537,
    key_size = 2048,
)

public_key = private_key.public_key()
xylem_remote_public_key = None
ws_send_queue = queue.Queue()
ws_recv_queue = queue.Queue()
routing_msg_queue = queue.Queue()
service_dict = {}


def init_encrypt_with_private_key(message):
    try:
        encrypted = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        xr_handler_logger.error(f"Encryption with client private key failed: {e}")
        return None
    

def init_encrypt_with_xylem_remote_public_key(message):
    global xylem_remote_public_key
    try:
        aes_key = urandom(32)
        iv = urandom(16)
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        pad_length = 16 - len(message) % 16
        message_padded = message + chr(pad_length) * pad_length
        encrypted_message = encryptor.update(message_padded.encode()) + encryptor.finalize()
        encrypted_aes_key = xylem_remote_public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return json.dumps({
            'encrypted_message': base64.b64encode(encrypted_message).decode(),
            'encrypted_aes_key': base64.b64encode(encrypted_aes_key).decode(),
            'iv': base64.b64encode(iv).decode()
        })
    except Exception as e:
        xr_handler_logger.error(f"Encryption with server's public key failed: {e}")
        return None


def basic_encryption_with_xylem_remote_public_key(message):
    global xylem_remote_public_key
    aes_key = os.urandom(32)
    iv = os.urandom(12)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(iv, message.encode(), None)
    encrypted_key = xylem_remote_public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return json.dumps({
        "encrypted_key": encrypted_key.hex(),
        "iv": iv.hex(),
        "ciphertext": ciphertext.hex()
    }).encode()


def basic_decryption_with_private_key(ciphertextbytes):
    encrypted_package = json.loads(ciphertextbytes.decode())
    encrypted_key = bytes.fromhex(encrypted_package["encrypted_key"])
    iv = bytes.fromhex(encrypted_package["iv"])
    ciphertext = bytes.fromhex(encrypted_package["ciphertext"])
    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(iv, ciphertext, None).decode()


async def perform_handshake(websocket):
    global xylem_remote_public_key

    try:
        # 1️ Client → Server : client public key
        await websocket.send(
            public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
        xr_handler_logger.info("Client public key sent")

        # 2️ Server → Client : server public key
        server_pub_bytes = await websocket.recv()
        xylem_remote_public_key = serialization.load_der_public_key(server_pub_bytes)
        xr_handler_logger.info("Server public key received")

        # 3 Client → Server : encrypted passkey
        first = init_encrypt_with_private_key(serve.xylem_remote_ws_pass_key)
        encrypted_pass = init_encrypt_with_xylem_remote_public_key(first)

        await websocket.send(encrypted_pass.encode())
        xr_handler_logger.info("Encrypted passkey sent")

        # 4 Server → Client : status
        response = await websocket.recv()
        decrypted = basic_decryption_with_private_key(response)
        data = json.loads(decrypted)

        if data.get("status") != 100:
            xr_handler_logger.error(f"Handshake rejected: {data}")
            return False

        return True

    except Exception:
        xr_handler_logger.exception("Handshake exception")
        return False


async def connect_websocket(uri):
    global xylem_remote_public_key

    while True:
        try:
            xr_handler_logger.info("Connecting to XYLEM REMOTE...")

            async with websockets.connect(uri) as websocket:

                xr_handler_logger.info("Socket connected")

                ok = await perform_handshake(websocket)

                if not ok:
                    xr_handler_logger.error("Handshake failed. Closing socket.")
                    await websocket.close()
                    continue

                xr_handler_logger.info("Handshake SUCCESS")

                send_task = asyncio.create_task(send_loop(websocket))
                recv_task = asyncio.create_task(receive_loop(websocket))

                await websocket.wait_closed()

                send_task.cancel()
                recv_task.cancel()

        except Exception as e:
            xr_handler_logger.error(f"Connection error: {e}")

        await asyncio.sleep(serve.error_wait)


async def send_loop(websocket):
    while True:
        try:
            data = ws_send_queue.get_nowait()

            await websocket.send(
                basic_encryption_with_xylem_remote_public_key(
                    json.dumps(data)
                )
            )

            xr_handler_logger.info(f"Sent: {data}")

        except queue.Empty:
            pass
        except Exception:
            xr_handler_logger.exception("Send failed")

        await asyncio.sleep(0.05)


async def receive_loop(websocket):
    try:
        while True:
            response = await websocket.recv()
            decrypted = basic_decryption_with_private_key(response)

            xr_handler_logger.info(f"Received: {decrypted}")

            routing_msg_queue.put(json.loads(decrypted))

    except ConnectionClosedOK:
        xr_handler_logger.info("Socket closed normally")

    except ConnectionClosedError as e:
        xr_handler_logger.warning(f"Socket closed: {e.code} {e.reason}")

    except Exception:
        xr_handler_logger.exception("Receive loop error")


def route_message():
    while True:
        xr_data = routing_msg_queue.get()
        xr_handler_logger.info(f"Routing message: {xr_data}")
        try:           
            s000_service = serve.XylemRemoteServices.S000XylemRemoteMaster
            s001_service = serve.XylemRemoteServices.S001XylemRemoteApproval
            s000_service_name = s000_service.name
            s001_service_name = s001_service.name         
            if xr_data["service_code"] in s000_service.codes:
                target_service = s000_service
                target_service_name = s000_service_name
            elif xr_data["service_code"] in s001_service.codes:
                target_service = s001_service
                target_service_name = s001_service_name
            else:
                xr_data["validation"] = s000_service.Validation.invalid_request.code
                ws_send_queue.put(xr_data)
                continue

            # S000 ROUTING (Login / Master flow)
            if target_service == s000_service:
                xr_handler_logger.info("Routing to S000 service")
                if s000_service_name not in service_dict:
                    service_dict[s000_service_name] = {}
                service_dict[s000_service_name][xr_data["session_key"]] = {
                    "xr_data": copy.deepcopy(xr_data),
                    "last_activity": datetime.datetime.now(),
                    "del_session": None
                }
                serve.Apps.A000XylemMaster.xrh_app_queue.put(xr_data)
                continue   

            # S001 ROUTING (Approval flow)          
            if (target_service_name in service_dict and xr_data["session_key"] in service_dict[target_service_name]):
                # Existing session
                last_xr_data = service_dict[target_service_name][xr_data["session_key"]]["xr_data"]
                if ("validation" in last_xr_data and last_xr_data["validation"] == s001_service.Validation.ok.code):
                    completed_progress = serve.get_progress_level_by_key(last_xr_data["progress_key"])
                    current_progress = serve.get_progress_level_by_key(xr_data["progress_key"])
                    if (completed_progress + 1 != current_progress and current_progress != s001_service.Progress.validate_form.code):
                        xr_data["validation"] = (s001_service.Validation.previous_validation_not_done.code)
                        service_dict[target_service_name][xr_data["session_key"]]["del_session"] = True
                        ws_send_queue.put(xr_data)
                        continue
                # Update session
                service_dict[target_service_name][xr_data["session_key"]] = {
                    "xr_data": copy.deepcopy(xr_data),
                    "last_activity": datetime.datetime.now(),
                    "del_session": None
                }
                app, token = serve.extract_app_linked_token(xr_data["token"])
                app.xrh_app_queue.put(xr_data)
                continue
            else:
                # New S001 session must start with validate_form
                progress_level = serve.get_progress_level_by_key(xr_data["progress_key"])
                if progress_level == s001_service.Progress.validate_form.code:
                    if target_service_name not in service_dict:
                        service_dict[target_service_name] = {}
                    service_dict[target_service_name][xr_data["session_key"]] = {
                        "xr_data": copy.deepcopy(xr_data),
                        "last_activity": datetime.datetime.now(),
                        "del_session": None
                    }
                    app, token = serve.extract_app_linked_token(xr_data["token"])
                    app.xrh_app_queue.put(xr_data)
                    continue
                else:
                    xr_data["validation"] = (s001_service.Validation.previous_validation_not_done.code)
                    ws_send_queue.put(xr_data)
                    continue
        except Exception:
            xr_handler_logger.error("Exception occurred", exc_info=True)


def remove_idle_sessions():
    while True:
        try:
            current_time = datetime.datetime.now()
            service_name = serve.XylemRemoteServices.S001XylemRemoteApproval.name
            session_keys = list(service_dict[service_name].keys()) if service_name in service_dict else []
            for session_key in session_keys:
                session = service_dict[service_name][session_key]
                if session["del_session"]:
                    del service_dict[service_name][session_key]
                    xr_handler_logger.info(f"Removed ended or invalid session: {session_key}")
                elif (current_time - session["last_activity"]).total_seconds() > serve.xyelm_remote_ws_session_timeout_in_secs:
                    del service_dict[service_name][session_key]
                    xr_handler_logger.info(f"Removed idle session: {session_key}")
        except Exception as e:
            xr_handler_logger.error("Exception occurred", exc_info=True)
        time.sleep(0.1)


def start_xylem_remote_ws(uri):
    asyncio.run(connect_websocket(uri))


serve.run_as_thread(start_xylem_remote_ws, args = (serve.xylem_remote_ws_uri,))
serve.run_as_thread(route_message)
serve.run_as_thread(remove_idle_sessions)
