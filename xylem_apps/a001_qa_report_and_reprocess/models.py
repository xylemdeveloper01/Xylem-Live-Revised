from django.db import models

# Create your models here.
class ReprocessRecordLog(models.Model):
    ID = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=10)
    serialno = models.CharField(max_length=50)
    db_name = models.CharField(max_length=20)
    table_name = models.CharField(max_length=10)
    datetime = models.DateTimeField(auto_now=True)
    i_remarks = models.PositiveIntegerField(null=True)
