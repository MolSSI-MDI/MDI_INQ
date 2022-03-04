import mdi
from mdi import MDI_NAME_LENGTH, MDI_COMMAND_LENGTH
import sys
from mpi4py import MPI


# This function is called by the MDI Library, not by this Driver
# It wraps the PluginInstance.callback function for the MDI Library,
#    which cannot directly call class functions.
def callback_wrapper(mpi_comm, mdi_comm, class_object):
    return class_object.callback(mpi_comm, mdi_comm)


class PluginInstance:


    def __init__(self):

        # Set system information for this plugin run
        # For some engines, this information will be sent via MDI
        # For others, this information must be read in the engine's input file
        self.cell = [
            12.0, 0.0, 0.0,
            0.0, 12.0, 0.0,
            0.0, 0.0, 12.0 ]
        self.elements = [ 8, 1, 1 ]    
        self.coords = [
            0.0, -0.553586, 0.0,
            1.429937, 0.553586, 0.0,
            -1.429937, 0.553586, 0.0
            ]
        self.natoms = len( self.elements )


    # launch the plugin
    def launch(self, plugin_name, command_line, mpi_world):

        mdi.MDI_Launch_plugin(plugin_name,
                      str(command_line) + " -mdi \"-name MM -role ENGINE -method LINK\"",
                      mpi_world,
                      callback_wrapper,
                      self)


    # This function is called by the MDI Library, not by this Driver
    # It contains the commands that should be sent to the engine
    def callback(self, mpi_comm, mdi_comm):

        mdi.MDI_Send_Command("<NAME", mdi_comm)
        name = mdi.MDI_Recv(mdi.MDI_NAME_LENGTH, mdi.MDI_CHAR, mdi_comm)
        print("Engine name: " + str(name))

        mdi.MDI_Send_Command(">CELL", mdi_comm)
        mdi.MDI_Send(self.cell, 9, mdi.MDI_DOUBLE, mdi_comm)

        mdi.MDI_Send_Command("<CELL", mdi_comm)
        self.cell = mdi.MDI_Recv(9, mdi.MDI_DOUBLE, mdi_comm)
        print("Cell: " + str(self.cell))

        mdi.MDI_Send_Command(">NATOMS", mdi_comm)
        mdi.MDI_Send(self.natoms, 1, mdi.MDI_INT, mdi_comm)

        mdi.MDI_Send_Command(">ELEMENTS", mdi_comm)
        mdi.MDI_Send(self.elements, self.natoms, mdi.MDI_INT, mdi_comm)

        mdi.MDI_Send_Command(">COORDS", mdi_comm)
        mdi.MDI_Send(self.coords, 3*self.natoms, mdi.MDI_DOUBLE, mdi_comm)

        mdi.MDI_Send_Command("<ENERGY", mdi_comm)
        energy = mdi.MDI_Recv(1, mdi.MDI_DOUBLE, mdi_comm)
        print("ENERGY: " + str(energy))
        
        mdi.MDI_Send_Command("<FORCES", mdi_comm)
        forces = mdi.MDI_Recv(3*self.natoms, mdi.MDI_DOUBLE, mdi_comm)
        print("FORCES: " + str(forces))

        # Send the "EXIT" command to the engine
        mdi.MDI_Send_Command("EXIT", mdi_comm)

        return 0



iarg = 1
while iarg < len(sys.argv):
    arg = sys.argv[iarg]

    if arg == "-mdi":
        # Initialize MDI
        if len(sys.argv) <= iarg+1:
            raise Exception("Argument to -mdi option not found")
        mdi.MDI_Init(sys.argv[iarg+1])
        iarg += 1
    else:
        raise Exception("Unrecognized argument")

    iarg += 1


plugin_name = "inqmdi"
mpi_world = MPI.COMM_WORLD
engine_command_line = ""


for i in range(2):
    plugin = PluginInstance()
    plugin.launch(plugin_name, engine_command_line, mpi_world)



