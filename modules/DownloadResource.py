import datetime
import urllib
import threading

# Common packages
from modules.common.TqdmUpTo import TqdmUpTo

# Decorator for the threading parameter.
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


# Generic class to download a specific URI
# TODO: execute_download requires a dict("uri","output_filename"). Add a function to check the input
class DownloadResource(object):

    def __init__(self, output_dir):
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.output_dir = output_dir

    def replace_suffix(self, args):
        if args.suffix:
            self.suffix = args.suffix

    def filename(self, param_filename):
        return self.output_dir+'/'+param_filename.replace('{suffix}', self.suffix)

    def execute_download(self, resource_info):
        print "Start to download\n\t{uri} data ".format(uri=resource_info["uri"])
        try:
            download = urllib.URLopener()
            with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                          desc=resource_info["uri"].split('/')[-1]) as t:  # all optional kwargs
                download.retrieve(resource_info["uri"], self.filename(resource_info["output_filename"]),
                                  reporthook=t.update_to)
        except IOError as io_error:
            print "IOError: {io_error}".format(io_error=io_error)
        except Exception as e:
            print "Error: {msg}".format(msg=e)

    @threaded
    def execute_download_threaded(self, resource_info):
        self.execute_download(resource_info)
        
        
     

        





    
    
    
    
    def perform_action(self):
        data = {}
        
        
        try:
            response = requests.get(endpoint)
             # I can use r.json(). I prefer to convert the data with the standard json library json.loads(response.text)
            data=response.text  
        except requests.exceptions.ConnectionError as error:
            # If the the url is wrong the requests package raises specific error.
            # Eg url is https://www.targetvalidation.com/api/latest/public/stats to raise this exception.
            # Store exception error using message key. I reuse our structure
            data['message'] = error
        return data

    # Param has to be structured as: {action : value}.
    # Using the argument passed by command line the action can be target/disease and the value is the command line imput
    def execute(self, param):
        endpoint ='{}?{}={}'.format(self.server,next(iter(param)),param.values()[0]) #the dict contains only an single key/value
        response = self.perform_rest_action(endpoint)

        #something went wrong. The response is build using message field to raise internal error too.
        if 'message' in response:
            print response
            response = None

        return response
    
        
    
    


