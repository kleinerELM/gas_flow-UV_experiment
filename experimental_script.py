import serial
import time, glob, sys
from datetime import datetime
import propar

# experimental parameters
on_time  = 10# in Sekunden
off_time = 10# in Sekunden
v_NO_values = [1.2, 2.4, 4.8, 9.6, 12.0] # valve flow in %

# system parameters
Bronhorst_COM = 'COM1'
Lamp_COM      = 'COM4'

# valve definitions in BH_dev_lib
# 'abritrary name': {'device': device object provided by propar
#                    'serial': serial number of the valve for identification purposes
#                    'state1': in % - Off state
#                    'state2': in % - standard on state
#                    'found': True if the device is present, False, if not (yet) found
#                    'desc': free text to describe the purpose of the valve
BH_dev_lib = {
    'v_dry': {'device': None, 'serial': 'M21213512A', 'state1': 0, 'state2': 6.0, 'found': False, 'desc': 'Luft trocken' },
    'v_hum': {'device': None, 'serial': 'M21213512B', 'state1': 0, 'state2': 6.0, 'found': False, 'desc': 'Luft feucht' },
    'v_NO' : {'device': None, 'serial': 'M21213512C', 'state1': 0, 'state2': 1.2, 'found': False, 'desc': 'NO' }
}

def programInfo():
    print("##########################################################")
    print("# small script to operate some valves and a UV-Lamp via  #")
    print("# serial port                                            #")
    print("#                                                        #")
    print("# © 2022 Florian Kleiner                                 #")
    print("#   Bauhaus-Universität Weimar                           #")
    print("#   Finger-Institut für Baustoffkunde                    #")
    print("#                                                        #")
    print("##########################################################")
    print()
    
# function to search for available serial ports
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

#Bronkhorst-stuff
known_devices = {}
for key, dev in BH_dev_lib.items(): known_devices[dev['serial']] = key

# find all valves by Bronkhorst and compare to the given valves
def BH_list_valves():
    # Connect to the local instrument.
    el_flow = propar.instrument(Bronhorst_COM)

    # Use the get_nodes function of the master of the instrument to get a list of instruments on the network
    nodes = el_flow.master.get_nodes()
    print("found {} Bronkhorst instruments.".format(len(nodes)))
    # Display the list of nodes
    for node in nodes:
        #print('  device #{}: {} ({})'.format(node['address'], node['type'], node['serial']) )
        if node['serial'] in known_devices:
            BH_dev_lib[ known_devices[node['serial']] ]['found'] = True
            BH_dev_lib[ known_devices[node['serial']] ]['device'] = propar.instrument(Bronhorst_COM, node['address'])
         else:
            print('  unknown device #{}: {} ({})'.format(node['address'], node['type'], node['serial']) )
            

    for dev in BH_dev_lib.values():
        if dev['found']:
            print('  Valve "{}" found.'.format(dev['desc']) )
        else:
            raise ConnectionError('Valve "{}" not found!'.format(dev['desc']))

    print()
    return el_flow

## lapstuff
last_time = ''
def cur_time():
    global last_time
    
    now = datetime.now()
    time = now.strftime("%d.%m.%Y %H:%M:%S")
    output = time+':' if time != last_time else ' '*20
    last_time = time
    return output

def toLamp( str ):
    print( '{} UV-Lamp turned {}'.format( cur_time(), str ) )
    port.write(str.encode())

def turn_on_UVLamp():
    toLamp('On')

def turn_off_UVLamp():
    toLamp('Off')

def check_valve_state(valve):
    # initial check of paramters of the Bronkhorst valves      
    params = [{'proc_nr':  33, 'parm_nr':  0, 'parm_type': propar.PP_TYPE_FLOAT},  # fmeasure (measured value indicates the amount of mass flow or pressure metered)
              {'proc_nr':  33, 'parm_nr':  3, 'parm_type': propar.PP_TYPE_FLOAT},  # fsetpoint (Setpoint is used to tell the instrument what the wanted amount of mass flow or pressure is)
              {'proc_nr':   1, 'parm_nr':  1, 'parm_type': propar.PP_TYPE_INT16},  # setpoint (Setpoint is used to tell the instrument what the wanted amount of mass flow or pressure is)
              {'proc_nr':  33, 'parm_nr':  7, 'parm_type': propar.PP_TYPE_FLOAT}]  # temperature
    
    values = valve['device'].read_parameters(params)
    print('{} valve "{}"  valve output: {:.2f} % (target: {:.2f} %), Temp: {:.1f} °C'.format(cur_time(), valve['desc'], values[0]['data']*10, values[2]['data']/320, values[3]['data']) ) # why to I have to multiply this value by 10??

def set_valve_value( valve, val ):
    target_value = int(32000/100*val)
    print('{} valve "{}"  valve set to: {:.2f} %'.format(cur_time(), valve['desc'], target_value/320) )
    params = [{'proc_nr': 1, 'parm_nr': 1, 'parm_type': propar.PP_TYPE_INT16, 'data': target_value}]
    # Write parameters returns a propar status code.
    status = valve['device'].write_parameters(params)
    if status != 0: print("failed to set {}! ",valve['desc'], status)

def set_valve_state( valve, state ):
    set_valve_value( valve, valve[state] )


### actual program start
if __name__ == '__main__':
    programInfo():
    print("Hi Dr. Torben!")
    print()
    
    available_ports = serial_ports()
    ports_available = False
    if not Bronhorst_COM in available_ports:
        raise ConnectionError( 'EL-Flow valves ({}) are not connected! Available ports:'.format(Bronhorst_COM), available_ports)
    else: 
        el_flow = BH_list_valves()

        if not Lamp_COM in available_ports:
            raise ConnectionError( 'Lamp-microcontroller ({}) is not connected! Available ports:'.format(Lamp_COM), available_ports)
        else: 
            port = serial.Serial(Lamp_COM, 115200, timeout=1)
            ports_available = True
    
    if ports_available:
        print("Basic settings:")
        on_time_str  = "{} min".format(int( on_time/60 ))  if (on_time > 60)  else "{} s".format(int( on_time  ))
        print("  Lamp On-time: {}".format(on_time_str))
        off_time_str = "{} min".format(int( off_time/60 )) if (off_time > 60) else "{} s".format(int( off_time ))
        print("  Lamp Off-time: {}".format(off_time_str))
        print("  Lamp will be turned on {} times".format(cycle_count))
        print()

        wait_n_sec = 2
       
        print("  waiting {} seconds. Cancel with [Ctrl]+[C]...".format(wait_n_sec))

        time.sleep(wait_n_sec)
        start_time = datetime.now()
        print()
        print("{} Starting experiment ({} steps)".format( start_time.strftime("%d.%m.%Y %H:%M:%S"), len(v_NO_values) ))
        date_finished = start_time + datetime.timedelta(0, (off_time + on_time)*len(v_NO_values) )
        print( 'The experiment will propably be finished at {}'.format(date_finished.strftime("%d.%m.%Y %H:%M")) )
         
        
        # initial check of paramters of the Bronkhorst valves
        for dev in BH_dev_lib.values():
            set_valve_state(dev, 'state2') # state 2 is the standard "open" value of all three valves
            
        print("initial valve check:")
        for dev in BH_dev_lib.values():
            check_valve_state(dev)
        print()
        
        time.sleep(1)
        for x in range(len(v_NO_values)):
            print("{} Cycle #{:02d}".format(cur_time(), x+1 ))
            # purge the chamber without UV lamp
            turn_off_UVLamp()
            set_valve_value( BH_dev_lib['v_NO'], v_NO_values[x] )
            wait_n_sec = 2
            time.sleep(wait_n_sec) # wait n seconds until the valve was able to set the value...
            check_valve_state(BH_dev_lib['v_NO'])
            time.sleep(off_time-wait_n_sec) # let the lamp off and purge the chamber for the defined time

            print()
            
            # turn the UV lamp on, when the gasflow is stable
            check_valve_state(BH_dev_lib['v_NO'])
            turn_on_UVLamp()
            time.sleep(on_time) # let the lamp on for the defined time

            print('-'*40)
        
        turn_off_UVLamp()

        difference = datetime.now() - start_time
        time_diff = divmod(difference.days * 24 * 60 * 60 + difference.seconds, 60)
        print("Experiment finished within {} min and {} sec".format(time_diff[0], time_diff[1]))
        print()
        input("Press Enter to close the experiment...")

    print("Script done.")
