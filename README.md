# gas_flow-UV_experiment

## microcontroller
The folder `Serial-relais` contains the code for a Node-mcu to switch a relais. In this project, the relais was used to toggle the UV lamp.
A NodeMCU v2 was used. The relais data pin was connected to Pin **D1**.
To turn the relais on, send the string "*On*" via a serial connection or "*Off*" to turn the Lamp off.

## main python script
The script `experimental_script.py` contains the experiment. The script controls bronkhorst gas flow valves and the mentioned UV-lamp. The purpose of the experiment is to measure gas (NO) decomposition on UV reactive surfaces.

## note
For some reason the measured values for the air valves have to be multiplied by a factor of 10 to  acquire the actual airflow.