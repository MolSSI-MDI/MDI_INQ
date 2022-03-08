/* -*- indent-tabs-mode: t -*- */

/*
 Copyright (C) 2019 Xavier Andrade

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.
  
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.
  
 You should have received a copy of the GNU Lesser General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
*/

#include <inq/inq.hpp>

int main(int argc, char ** argv){

	using namespace inq;
	using namespace inq::input;
	using namespace inq::magnitude;

        // attempt to initialize MPI without initializing an environment	
	MPI_Init(&argc, &argv);
        boost::mpi3::environment::named_attributes_key_f() = std::make_unique<boost::mpi3::communicator::keyval<std::map<std::string, boost::mpi3::any>>>();

	auto distance = 1.06_angstrom;

	std::vector<atom> geo;
	geo.push_back( "N" | coord(0.0, 0.0, -distance/2));
	geo.push_back( "N" | coord(0.0, 0.0,  distance/2));

	auto box = systems::box::orthorhombic(10.0_b, 10.0_b, 12.0_b).finite().cutoff_energy(40.0_Ha);
	
	systems::ions ions(box, geo);

        // get the communicator without using environment
        MPI_Comm mpi_world_comm = MPI_COMM_WORLD;
        systems::electrons electrons(boost::mpi3::grip(mpi_world_comm), ions, box);
        ground_state::initial_guess(ions, electrons);

        // run the calculation	
        auto scf_options = scf::conjugate_gradient() | scf::energy_tolerance(1.0e-5_Ha) | scf::density_mixing() | scf::broyden_mixing() | scf::calculate_forces();
        auto result = inq::ground_state::calculate(ions, electrons, interaction::dft(), scf_options);

	std::cout << "N2 energy = " << result.energy.total() << std::endl;

        // Finalize MPI
        boost::mpi3::environment::named_attributes_key_f().reset();
	MPI_Finalize();
}

