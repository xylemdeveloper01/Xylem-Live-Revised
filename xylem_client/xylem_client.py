import os, sys, time, threading, queue, socket, psutil, snap7, fins.udp, configparser, logging
from aphyt import omron
from logging.handlers import RotatingFileHandler

exec(open("tran_xylem_client.py").read())