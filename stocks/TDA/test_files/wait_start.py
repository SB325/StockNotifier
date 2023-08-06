from datetime import datetime, date
import pause

def wait_start(runTime):
    Time = runTime.split(':')
    t = date.today()
    print('Waiting for start time ' + runTime + '.')
    pause.until(datetime(t.year, t.month, t.day, int(Time[0]),int(Time[1])))
    print('Done waiting!')

