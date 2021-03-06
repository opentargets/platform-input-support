import logging
import psutil

import pyspark
import pyspark.sql
import pyspark.sql.functions
from pyspark import *
from pyspark.sql import *
from pyspark.sql.types import *
from pyspark.sql.functions import *

logger = logging.getLogger(__name__)

# This class is just a draft. All the compute should be done using:
# platform-etl-backend
# Todo: pass the pameters for cores and memory. Provide default.
class SparkHelpers(object):

    def __init__(self):
        self.pyspark_mem_available=str((psutil.virtual_memory().available) >>30)+'g'
        self.pyspark_core_max = str(psutil.cpu_count())
        self.pyspark_core_executor = str(psutil.cpu_count())
        self.session = None

    # Todo: add config parameters for cores and memory.
    def spark_init(self):
        conf = pyspark.SparkConf().setAll([('spark.executor.memory', self.pyspark_mem_available),
                                           ('spark.executor.cores', self.pyspark_core_executor),
                                           ('spark.cores.max', self.pyspark_core_max),
                                           ('spark.driver.memory', self.pyspark_mem_available)])
        sc = pyspark.SparkContext(conf=conf)
        #sc.getConf().getAll()
        self.session = SQLContext(sc)


    # Load different type of files. Eg. json, tab, parquet, cvs.
    # For cvs or tsv it is mandatory to add the separator = "\t" or ","
    def load_file(self, filename, extension, header = "false", separator = None):
        if separator is None:
            return self.session.read.format(extension).load(filename)
        else:
            return self.session.read.format(extension).option("header", header).option("sep", separator).load(filename)
