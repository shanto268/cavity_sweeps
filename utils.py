"""
========================================================================================================================
This file contains utility functions for the simulation.
========================================================================================================================
"""
from qiskit_metal import draw, Dict, designs, MetalGUI
from qiskit_metal.toolbox_metal import math_and_overrides
from qiskit_metal.qlibrary.core import QComponent
import qiskit_metal as metal
from just_claw import TransmonClaw
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors
from qiskit_metal.qlibrary.tlines.mixed_path import RouteMixed
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.couplers.cap_n_interdigital_tee import CapNInterdigitalTee
from qiskit_metal.qlibrary.couplers.line_tee import LineTee

from collections import OrderedDict

import numpy as np
from pyaedt import Hfss


def getMeshScreenshot(projectname,designname,solutiontype="Eigenmode"):
    """Interfaces w/ ANSYS via pyEPR for more custom automation.
    1. Connect to ANSYS
    2. Change Silicon permitivity to 11.45; represents ultra cold silicon.
    3. Checks for prexisting Setups, deletes them...
    """

    hfss = Hfss(projectname=projectname, 
                designname=designname, 
                solution_type=solutiontype,
                new_desktop_session=False, 
                close_on_exit=False)


    # Speculative command to show the mesh in the HFSS graphical interface
    #hfss.oeditor.ShowWindow(["NAME:WindowParameters", "ShowMesh:=", True])

    # Export the design preview to a JPG file
    #hfss.export_design_preview_to_jpg('output.jpg')

    mesh_view_script = """
    oDesktop.RestoreWindow
    o3DLayout = oProject.SetActiveEditor("3D Modeler")
    o3DLayout.ShowWindow("Mesh")
    """

    hfss.oeditor.AddScriptCommand(mesh_view_script, True)

    # Export the design preview to a JPG file
    hfss.export_design_preview_to_jpg('output2.jpg')

def generate_bbox(component: QComponent) -> Dict[str, float]:
    """
    Generates a bounding box dictionary from a given QComponent.

    Parameters:
    component (QComponent): The component for which to generate a bounding box.

    Returns:
    Dict[str, float]: A dictionary representing the bounding box with keys 'min_x', 'max_x', 'min_y', 'max_y'.
    """
    bounds = component.qgeometry_bounds()
    bbox = {
        'min_x': bounds[0],
        'max_x': bounds[2],
        'min_y': bounds[1],
        'max_y': bounds[3]
    }
    return bbox

def setMaterialProperties(projectname,designname,solutiontype="Eigenmode"):
    """Interfaces w/ ANSYS via pyEPR for more custom automation.
    1. Connect to ANSYS
    2. Change Silicon permitivity to 11.45; represents ultra cold silicon.
    3. Checks for prexisting Setups, deletes them...
    """

    aedt = Hfss(projectname=projectname, 
                designname=designname, 
                solution_type=solutiontype,
                new_desktop_session=False, 
                close_on_exit=False)


    ultra_cold_silicon(aedt)
    delete_old_setups(aedt)

    aedt.release_desktop(close_projects=False, close_desktop=False)

def ultra_cold_silicon(aedt):
    """Change silicon properties to ultra cold silicon

    Args:
        aedt (pyAEDT Desktop obj)
    """
    materials = aedt.materials
    silicon = materials.checkifmaterialexists('silicon')
    silicon.permittivity = 11.45
    silicon.dielectric_loss_tangent = 1E-7

def delete_old_setups(aedt):
    """Delete old setups

    Args:
        aedt (pyAEDT Desktop obj)
    """
    # Clear setups
    if len(aedt.setups) != 0:
        aedt.setups[0].delete()

def calculate_center_and_dimensions(bbox):
    """
    Calculate the center and dimensions from the bounding box.

    :param bbox: The bounding box dictionary with keys 'min_x', 'max_x', 'min_y', 'max_y'.
    :return: A tuple containing the center coordinates and dimensions.
    """
    center_x = (bbox['min_x'] + bbox['max_x']) / 2 
    center_y = (bbox['min_y'] + bbox['max_y']) / 2 
    center_z = 0

    x_size = bbox['max_x'] - bbox['min_x']  
    y_size = bbox['max_y'] - bbox['min_y']
    z_size = 0

    return (center_x, center_y, center_z), (x_size, y_size, z_size)

def get_freq(epra, test_hfss):
    """
    Analyze the simulation, plot the results, and report the frequencies, Q, and kappa.

    :param epra: The EPR analysis object.
    :param test_hfss: The HFSS object.
    """
    project_name = test_hfss.pinfo.project_name
    design_name = test_hfss.pinfo.design_name

    setMaterialProperties(project_name, design_name, solutiontype="Eigenmode")
    epra.sim._analyze()
    try:
        epra.sim.plot_convergences()
        epra.sim.save_screenshot()
        epra.sim.plot_fields('main')
        epra.sim.save_screenshot()
    except:
        print("couldn't generate plots.")
    f = epra.get_frequencies()

    freq = f.values[0][0] * 1e9
    print(f"freq = {round(freq/1e9, 3)} GHz")
    return freq


def get_freq_Q_kappa(epra, test_hfss):
    """
    Analyze the simulation, plot the results, and report the frequencies, Q, and kappa.

    :param epra: The EPR analysis object.
    :param test_hfss: The HFSS object.
    """
    project_name = test_hfss.pinfo.project_name
    design_name = test_hfss.pinfo.design_name

    setMaterialProperties(project_name, design_name, solutiontype="Eigenmode")
    epra.sim._analyze()
    epra.sim.plot_convergences()
    epra.sim.save_screenshot()
    epra.sim.plot_fields('main')
    epra.sim.save_screenshot()
    f = epra.get_frequencies()

    freq = f.values[0][0] * 1e9
    Q = f.values[0][1]
    kappa = freq / Q
    print(f"freq = {round(freq/1e9, 3)} GHz")
    print(f"Q = {round(Q, 1)}")
    print(f"kappa = {round(kappa/1e6, 3)} MHz")
    return freq, Q, kappa

def mesh_objects(modeler, mesh_lengths):
    """
    Draw the rectangle in the Ansys modeler, update the model, and set the mesh based on the input dictionary.

    :param modeler: The modeler object.
    :param center: The center coordinates tuple.
    :param dimensions: The dimensions tuple.
    :param cpw: The cpw object.
    :param claw: The claw object.
    :param mesh_lengths: Dictionary containing mesh names, associated objects, and MaxLength values.
    """
    for mesh_name, mesh_info in mesh_lengths.items():
        modeler.mesh_length(mesh_name, mesh_info['objects'], MaxLength=mesh_info['MaxLength'])

def add_ground_strip_and_mesh(modeler, center, dimensions, coupler, cpw, claw, mesh_lengths):
    """
    Draw the rectangle in the Ansys modeler, update the model, and set the mesh based on the input dictionary.

    :param modeler: The modeler object.
    :param center: The center coordinates tuple.
    :param dimensions: The dimensions tuple.
    :param coupler: The coupler object.
    :param cpw: The cpw object.
    :param claw: The claw object.
    :param mesh_lengths: Dictionary containing mesh names, associated objects, and MaxLength values.
    """
    gs = modeler.draw_rect_center(
        [coord * 1e-3 for coord in center],
        x_size=dimensions[0] * 1e-3,
        y_size=dimensions[1] * 1e-3,
        name='ground_strip'
    )

    modeler.intersect(["ground_strip", "ground_main_plane"], True)
    modeler.subtract("ground_main_plane", ["ground_strip"], True)
    modeler.assign_perfect_E(["ground_strip"])

    for mesh_name, mesh_info in mesh_lengths.items():
        modeler.mesh_length(mesh_name, mesh_info['objects'], MaxLength=mesh_info['MaxLength'])

def create_claw(opts, design):
    claw = TransmonClaw(design, 'claw', options=opts)
    return claw

def create_coupler(opts, design):
    cplr = CapNInterdigitalTee(design, 'cplr', options = opts) if "finger_count" in opts.keys() else CoupledLineTee(design, 'cplr', options = opts)
    return cplr

def create_cpw(opts, design):
    opts.update({"pin_inputs" : Dict(start_pin = Dict(component = 'cplr',
                                                    pin = 'second_end'),
                                   end_pin = Dict(component = 'claw',
                                                  pin = 'readout'))})
    cpw = RouteMeander(design, 'cpw', options = opts)
    return cpw

if __name__ == "__main__":
    # Usage
    mesh_lengths = {
        'mesh1': {"objects": ["ground_strip"], "MaxLength": '4um'},
        'mesh2': {"objects": [f"prime_cpw_{coupler.name}", f"second_cpw_{coupler.name}", f"trace_{cpw.name}", f"readout_connector_arm_{claw.name}"], "MaxLength": '4um'},
        # 'mesh3': {"objects": [f"Port_{coupler.name}_prime_end", f"Port_{coupler.name}_prime_start"], "MaxLength": '4um'}
    }
    center, dimensions = calculate_center_and_dimensions(bbox)
    draw_and_update_model(modeler, center, dimensions, coupler, cpw, claw, mesh_lengths)
    get_freq_Q_kappa(epra, test_hfss)

