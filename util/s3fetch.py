import urllib

for i in range(100):
  print i
  
  try :
    urllib.urlretrieve("https://s3.amazonaws.com/thunder.datasets/test/stack-big/TM{:0>5}_CM0_CHN00.stack".format(i), filename="TM{:0>5}_CM0_CHN00.stack".format(i) )
  
  except Exception, e:
    print e
