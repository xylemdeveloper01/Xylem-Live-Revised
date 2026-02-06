import datetime, pyodbc, time, logging
from django.db import models
from django.core.cache import caches

from xylem_apps.a000_xylem_master import serve 

setting_file=open("./xylem_apps/a001_qa_report_and_reprocess/line_stn_settings.txt","r")
transfer_dict={}
for line in setting_file:
    file_data=line.strip().split("===")
    a=file_data[0]
    b=file_data[1]
    transfer_dict[a]=b
setting_file.close()

a001_bw_logger = logging.getLogger(serve.Apps.A001QAReportAndReprocess.bw_logger_name)

line_key_list = serve.Apps.A001QAReportAndReprocess.line_key_list
stn_key_list = serve.Apps.A001QAReportAndReprocess.stn_key_list

report_wt = serve.Apps.A001QAReportAndReprocess.report_wt
reprocess_wt = serve.Apps.A001QAReportAndReprocess.reprocess_wt

master_dict = {}
for i in range(10,99):
    str_i=str(i)
    if str_i in transfer_dict:
        temp_list1=transfer_dict[str_i].split(",")
        master_dict[i]={line_key_list[0]:temp_list1[0]}
        master_dict[i][line_key_list[1]]={}
        for j in temp_list1[1:]:
            if j in transfer_dict:
                int_j=int(j)
                temp_list2=transfer_dict[j].split(",")
                master_dict[i][line_key_list[1]][int_j]={}
                for k,v in zip(stn_key_list,temp_list2):
                    master_dict[i][line_key_list[1]][int_j][k]=v

a001_cache = caches[serve.an_qa_report_and_reprocess]
a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_master_dict, master_dict, timeout=None)

temp_list1=[]
temp_list2=[]
transfer_dict={}

server_connection_dict={}
reprocess_eligible_dict={}


def mainserver_connect(work_type,line_id,stn_id):
    global server_connection_dict,master_dict
    sql_instance_name=master_dict[line_id][line_key_list[1]][stn_id]["sql_instance_name"]
    user_name=master_dict[line_id][line_key_list[1]][stn_id]["user_name"]
    password=master_dict[line_id][line_key_list[1]][stn_id]["password"]
    database_name=master_dict[line_id][line_key_list[1]][stn_id]["database_name"]
    server_conn = pyodbc.connect(
        Driver="SQL Server",
        Server=sql_instance_name,
        Database=database_name,
        UID=user_name,
        PWD=password
    )
    server_cursor=server_conn.cursor()
    cid_i=1000
    while True:
        cid=str(cid_i)
        if  cid in server_connection_dict:
            cid_i=cid_i+1
        else:
            break
    server_connection_dict[cid]={"server_conn":server_conn,"server_cur":server_cursor,"work_type":work_type,"line_id":line_id,"stn_id":stn_id,"last_used_time":datetime.datetime.now()}
    a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_server_connection_dict, str(server_connection_dict), timeout=None)
    a001_bw_logger.info(f"SQL Server connected successfully [CID: {cid}]. LID:{line_id}, SID:{stn_id}")
    return cid


def mainserver_get_data(cid,serialno=None,fromDate=None,toDate=None):
    global server_connection_dict, master_dict, reprocess_eligible_dict
    work_type=server_connection_dict[cid]["work_type"]
    server_cur=server_connection_dict[cid]["server_cur"]
    line_id=server_connection_dict[cid]["line_id"]
    stn_id=server_connection_dict[cid]["stn_id"]
    table_name=master_dict[line_id][line_key_list[1]][stn_id]["table_name"]
    serialno_col_name=master_dict[line_id][line_key_list[1]][stn_id]["serialno_col_name"]
    datetime_col_name=master_dict[line_id][line_key_list[1]][stn_id]["datetime_col_name"]
    sort_by_col_name=master_dict[line_id][line_key_list[1]][stn_id]["sort_by_col_name"]
    result_col_name=master_dict[line_id][line_key_list[1]][stn_id]["result_col_name"]
    send_dict={}
    report_col_data=[]
    report_row_data=[]
    server_connection_dict[cid]["last_used_time"]=datetime.datetime.now()
    a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_server_connection_dict, str(server_connection_dict), timeout=None)
    if work_type==report_wt:
        if serialno:
            sqlquery=f""" SELECT * FROM [dbo].[{table_name}]
                        where {serialno_col_name}='{serialno}' 
                        order by {sort_by_col_name} Desc """
            server_cur.execute(sqlquery)
            report_row_data = server_cur.fetchall()
        elif fromDate or toDate:
            start_date = datetime.datetime.strptime(fromDate, "%Y-%m-%dT%H:%M")
            end_date = datetime.datetime.strptime(toDate, "%Y-%m-%dT%H:%M")
            sqlquery=f""" SELECT * FROM [dbo].[{table_name}]
                    where {datetime_col_name} between '{start_date}' and '{end_date}'
                    order by {sort_by_col_name} Desc """
            server_cur.execute(sqlquery)
            report_row_data = server_cur.fetchall()
        # else:
        #     print("All none received")
        if report_row_data:
            sqlquery=f""" SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('[{table_name}]') """
            server_cur.execute(sqlquery)
            report_col_data = server_cur.fetchall()
            for col_index,col in enumerate(report_col_data):    
                report_col_data[col_index]=col.name
            result_index = report_col_data.index(result_col_name)
            for row_index,row in enumerate(report_row_data):
                send_dict[row_index]={}
                for cell_index,cell in enumerate(row):
                    if result_index!=cell_index:
                        send_dict[row_index][report_col_data[cell_index]]=cell
                    else:
                        if not cell is None:
                            send_dict[row_index][report_col_data[cell_index]]=serve.get_icode_object(cell).name
                        else:
                            send_dict[row_index][report_col_data[cell_index]]=cell
    elif work_type==reprocess_wt:
        if serialno:
            sqlquery=f""" SELECT TOP(1) * FROM [dbo].[{table_name}]
                    where {serialno_col_name}='{serialno}'
                    order by {sort_by_col_name} Desc """
            server_cur.execute(sqlquery)
            report_row_data = server_cur.fetchone()
        # else:
        #     print("serialno none received")

        if report_row_data:
            send_dict["data"]={}
            send_dict["reprocess_status"]=None
            report_col_data = [column[0] for column in server_cur.description]
            result_col_name=master_dict[line_id][line_key_list[1]][stn_id]["result_col_name"]
            result_index = report_col_data.index(result_col_name)
            if result_col_name in report_col_data:
                result=report_row_data[result_index]
                if result==0:
                    send_dict["reprocess_status"]=True
                else:
                    send_dict["reprocess_status"]=False
                    reprocess_eligible_dict[serialno]=[report_col_data,report_row_data]
                    a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_reprocess_eligible_dict, reprocess_eligible_dict, timeout=None)
            for cell_index,cell in enumerate(report_row_data):
                if result_index!=cell_index:
                    send_dict["data"][report_col_data[cell_index]]=cell
                else:
                    send_dict["data"][report_col_data[cell_index]]=serve.get_icode_object(cell).name
    return send_dict


def mainserver_update_data(cid,serialNo,remarks):
    global server_connection_dict, master_dict, reprocess_eligible_dict
    work_type=server_connection_dict[cid]["work_type"]
    server_cur=server_connection_dict[cid]["server_cur"]
    line_id=server_connection_dict[cid]["line_id"]
    stn_id=server_connection_dict[cid]["stn_id"]
    database_name=master_dict[line_id][line_key_list[1]][stn_id]["database_name"]
    table_name=master_dict[line_id][line_key_list[1]][stn_id]["table_name"]
    # serialno_col_name=master_dict[line_id][line_key_list[1]][stn_id]["serialno_col_name"]
    sort_by_col_name=master_dict[line_id][line_key_list[1]][stn_id]["sort_by_col_name"]
    datetime_col_name=master_dict[line_id][line_key_list[1]][stn_id]["datetime_col_name"]
    result_col_name=master_dict[line_id][line_key_list[1]][stn_id]["result_col_name"]
    remarks_col_name=master_dict[line_id][line_key_list[1]][stn_id]["remarks_col_name"]
    work_type=server_connection_dict[cid]["work_type"]
    server_connection_dict[cid]["last_used_time"]=datetime.datetime.now()
    a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_server_connection_dict, str(server_connection_dict), timeout=None)
    a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_reprocess_eligible_dict, reprocess_eligible_dict, timeout=None)
    if work_type==reprocess_wt:
        if serialNo in reprocess_eligible_dict:
            col_data,row_data=reprocess_eligible_dict[serialNo]
            col_list=[]
            val_list=[]
            setattr(row_data, result_col_name, 0)
            setattr(row_data, datetime_col_name, "replace_updated_time")
            setattr(row_data, remarks_col_name, remarks)
            for col in col_data:
                if col == sort_by_col_name:
                    continue
                val=getattr(row_data, col)
                if val!=None:
                    col_list.append(col)
                    val_list.append(val)
            sql_query=f"""
                INSERT INTO [dbo].[{table_name}] ({",".join(col_list)})
                Values {str(tuple(val_list)).replace("'replace_updated_time'","getdate()")}"""
            server_cur.execute(sql_query)
            server_cur.commit()
            while serialNo in reprocess_eligible_dict:
                del reprocess_eligible_dict[serialNo]
                a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_reprocess_eligible_dict, reprocess_eligible_dict, timeout=None)
            return {"db_name":database_name,"table_name":table_name}
        else:
            return None
    return None


def remove_overtime_cid():
    while True:
        try:
            temp_list=[]
            for cid in server_connection_dict:
                if server_connection_dict[cid]["last_used_time"] <= datetime.datetime.now()-datetime.timedelta(minutes=5):
                    temp_list.append(cid)
            for cid in temp_list:
                a001_bw_logger.info(f"SQL Server connection closed [CID: {cid}] due to inactivity over 5 minutes.")
                server_connection_dict[cid]["server_cur"].close()
                server_connection_dict[cid]["server_conn"].close()
                del server_connection_dict[cid]
            if temp_list:
                a001_cache.set(serve.Apps.A001QAReportAndReprocess.cache_key_of_server_connection_dict, str(server_connection_dict), timeout=None)
            time.sleep(1)
        except Exception as e:
            a001_bw_logger.error(f"Error in removing overtime CID: {e}", exc_info=True)
            time.sleep(3)
            
serve.run_as_thread(remove_overtime_cid)