import datetime

datetime_string = bin_file_name.split('.')[0]
datetime_object = datetime.datetime.strptime(datetime_string, "%d-%m-%YT%H-%M-%S-%f")
bin_timestamp = datetime_object.strftime("%H_%M_%S")

