import triad_openvr
import time
import sys

v = triad_openvr.triad_openvr()
v.print_discovered_objects()

if len(sys.argv) == 1:
    interval = 1/250
elif len(sys.argv) == 2:
    interval = 1/float(sys.argv[1])
else:
    print("Invalid number of arguments")
    interval = False

if interval:
    while(True):
        start = time.time()
        txt = ""
        position = v.devices["controller_1"].get_pose_euler()

        if hasattr(position, '__iter__'):
            for each in position:
                txt += "%.4f" % each
                txt += " "
        else:
            txt = "Waiting for controller"
        print("\r" + txt, end="")
        sleep_time = interval-(time.time()-start)
        if sleep_time > 0:
            time.sleep(sleep_time)
