import serial
import time, glob, sys
from datetime import datetime
import propar

Bronhorst_COM = 'COM1'
Lamp_COM      = 'COM4'
on_time = 10# in Sekunden
off_time = 10# in Sekunden
cycle_count = 5

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

#el_flow = propar.Instrument(Bronhorst_COM, 1, baudrate=38400)

#el_flow.setpoint
#Bronkhorst-stuff

BH_dev_lib = {
    'v_dry': {'device': None, 'serial': 'M21213512A', 'state1': 0, 'state2': 6.0, 'found': False, 'desc': 'Luft trocken' },
    'v_hum': {'device': None, 'serial': 'M21213512B', 'state1': 0, 'state2': 6.0, 'found': False, 'desc': 'Luft feucht' },
    'v_NO' : {'device': None, 'serial': 'M21213512C', 'state1': 0, 'state2': 1.2, 'found': False, 'desc': 'NO' }
}
known_devices = {}
for key, dev in BH_dev_lib.items(): known_devices[dev['serial']] = key

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
    output = ' '*20
    now = datetime.now()
    time = now.strftime("%d.%m.%Y %H:%M:%S")
    if time != last_time: output = time+':'
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

def set_valve_state( valve, state ):
    target_value = int(32000/100*valve[state])
    print('{} valve "{}"  valve set to: {:.2f} %'.format(cur_time(), valve['desc'], target_value/320) )
    params = [{'proc_nr': 1, 'parm_nr': 1, 'parm_type': propar.PP_TYPE_INT16, 'data': target_value}]
    # Write parameters returns a propar status code.
    status = valve['device'].write_parameters(params)
    if status != 0: print("failed to set {}! ",valve['desc'], status)


### actual program start
if __name__ == '__main__':
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
        print("{} Starting experiment".format( start_time.strftime("%d.%m.%Y %H:%M:%S") ))
        
        # initial check of paramters of the Bronkhorst valves
        
        print("initial valve check:")
        for dev in BH_dev_lib.values():
            check_valve_state(dev)
        print()

        time.sleep(1)
        for x in range(cycle_count):
            print("{} Cycle #{:02d}".format(cur_time(), x+1 ))
            check_valve_state(BH_dev_lib['v_hum'])
            
            for dev in BH_dev_lib.values():
                set_valve_state(dev, 'state1')
            turn_off_UVLamp()            
            time.sleep(off_time * 1)

            print()

            for dev in BH_dev_lib.values():
                check_valve_state(dev)
            for dev in BH_dev_lib.values():
                set_valve_state(dev, 'state2')
            turn_on_UVLamp()
            time.sleep(on_time * 1)

            print('-'*20)
        
        turn_off_UVLamp()

        difference = datetime.now() - start_time
        time_diff = divmod(difference.days * 24 * 60 * 60 + difference.seconds, 60)
        print("Experiment finished within {} min and {} sec".format(time_diff[0], time_diff[1]))
        print()
        input("Press Enter to close the experiment...")

    print("Script done.")
