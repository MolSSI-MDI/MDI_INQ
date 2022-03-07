import mdi
import sys
import argparse
from mpi4py import MPI


# This function is called by the MDI Library, not by this Driver
# It wraps the PluginInstance.callback function for the MDI Library,
#    which cannot directly call class functions.
def callback_wrapper(mpi_comm, mdi_comm, class_object):
    return class_object.callback(mpi_comm, mdi_comm)


class PluginInstance:


    def __init__(self, cell_in, elements_in, coords_in):

        # Set system information for this plugin run
        self.cell = cell_in
        self.elements = elements_in  
        self.coords = coords_in
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
    
        my_rank = mpi_comm.Get_rank()

        mdi.MDI_Send_Command("<NAME", mdi_comm)
        name = mdi.MDI_Recv(mdi.MDI_NAME_LENGTH, mdi.MDI_CHAR, mdi_comm)
        if my_rank == 0:
            print("Engine name: " + str(name))

        # Send the cell dimensions to the plugin
        mdi.MDI_Send_Command(">CELL", mdi_comm)
        mdi.MDI_Send(self.cell, 9, mdi.MDI_DOUBLE, mdi_comm)

        # Find out if the plugin supports the >NATOMS command
        natoms_supported = 0
        natoms_supported = mdi.MDI_Check_command_exists("@DEFAULT", ">NATOMS", mdi_comm)
        natoms_supported = mpi_comm.bcast(natoms_supported, root=0)

        if natoms_supported:

            # Send the number of atoms to the plugin
            mdi.MDI_Send_Command(">NATOMS", mdi_comm)
            mdi.MDI_Send(self.natoms, 1, mdi.MDI_INT, mdi_comm)

        else:

            # We will assume the plugin has read the correct number
            #    of atoms from an input file.
            pass

        # Find out if the plugin supports the >ELEMENTS command
        elem_supported = 0
        elem_supported = mdi.MDI_Check_command_exists("@DEFAULT", ">ELEMENTS", mdi_comm)
        elem_supported = mpi_comm.bcast(elem_supported, root=0)

        if elem_supported:

            # Send the number of elements to the plugin
            mdi.MDI_Send_Command(">ELEMENTS", mdi_comm)
            mdi.MDI_Send(self.elements, self.natoms, mdi.MDI_INT, mdi_comm)

        else:

            # We will assume the plugin has read the correct element
            #    of each atom from an input file.
            pass

        # Send the nuclear coordinates to the plugin
        mdi.MDI_Send_Command(">COORDS", mdi_comm)
        mdi.MDI_Send(self.coords, 3*self.natoms, mdi.MDI_DOUBLE, mdi_comm)

        # Receive the energy of the system from the plugin
        mdi.MDI_Send_Command("<ENERGY", mdi_comm)
        energy = mdi.MDI_Recv(1, mdi.MDI_DOUBLE, mdi_comm)
        if my_rank == 0:
            print("ENERGY: " + str(energy))
        
        # Receive the nuclear forces from the plugin
        mdi.MDI_Send_Command("<FORCES", mdi_comm)
        forces = mdi.MDI_Recv(3*self.natoms, mdi.MDI_DOUBLE, mdi_comm)
        if my_rank == 0:
            print("FORCES: " + str(forces))

        # Send the "EXIT" command to the plugin
        mdi.MDI_Send_Command("EXIT", mdi_comm)

        return 0


# Parser for the input arguments
def create_parser():

    # Handle arguments with argparse
    parser = argparse.ArgumentParser(
        add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    required = parser.add_argument_group("Required Arguments")
    optional = parser.add_argument_group("Optional arguments")

    required.add_argument(
        "--mdi",
        help="Runtime options for the MDI Library.",
        type=str,
        required=True,
    )

    required.add_argument(
        "--plugin_name",
        help="Name of the MDI plugin to use.",
        type=str,
        required=True,
    )
    
    optional.add_argument(
        "--plugin_command_line",
        help="Command line arguments for the plugin to use.",
        type=str,
        default="",
    )
    
    return parser



# Parse the command-line arguments
parser = create_parser()
args = parser.parse_args()


# Initialize the MDI Library
mdi.MDI_Init( args.mdi )


# We'll try a simple calculation on a water molecule
cell = [
    12.0, 0.0, 0.0,
    0.0, 12.0, 0.0,
    0.0, 0.0, 12.0 ]
elements = [ 8, 1, 1 ]    
coords = [
    0.0, -0.553586, 0.0,
    1.429937, 0.553586, 0.0,
    -1.429937, 0.553586, 0.0
    ]


for i in range(2):
    plugin_mpi_comm = MPI.COMM_WORLD
    plugin = PluginInstance(cell, elements, coords)
    plugin.launch(args.plugin_name,
                  args.plugin_command_line,
                  plugin_mpi_comm)

    # Displace the oxygen in the +y direction
    coords[1] += 0.1



