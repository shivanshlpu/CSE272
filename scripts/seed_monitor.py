"""Create the user's selected initial monitor; no synthetic comments or analytics."""
from ml.monitor_store import MonitorStore
s=MonitorStore()
if not s.list():
    m=s.create({'name':"India’s Got Latent · S2 EP9",'target':'This episode of India’s Got Latent is entertaining and worth watching.','videos':['CswOUBuokjo'],'interval_seconds':300})
    print('Created monitor',m['id'])
else:print('Existing monitors retained')
