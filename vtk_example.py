# -*- coding: utf-8 -*-
__author__ = "Georgios E. Ragkousis"
import numpy as np
import matplotlib.pyplot as plt
import vtk
from pylsewave.pwconsts import *
from scipy.interpolate import UnivariateSpline, interp1d
from pylsewave.postprocessing import ExtractUVectors
import argparse as argprs


def vpwtkResMultiBlockFileWriter(ifilename, vessel_dict, vessel_map, ovisfile):

    # sampling frequency
    fr = 1  # kHz
    sampling_period = 0.001
    no_sampling_points = int(1.0 / 0.001)

    # results file
    myodbf = ExtractUVectors(ifilename)

    A = {}
    p = {}
    q = {}
    u = {}
    X = {}
    t = None
    XX = {}
    YY = {}
    for i in vessel_dict.keys():
        # print(i)
        A[i], q[i], p[i], u[i] = myodbf.getUVector(vessel_no=i, cycle=4, no_points=no_sampling_points)
        t = myodbf.meshgrid_T
        X = myodbf.meshgrid_X

        rws, clms = X.shape

        spatial_data = np.loadtxt('./data/Adan_vessel_topology_2D/' + str(vessel_map[i]) + 'vessel_points.dat', delimiter=',')
        x = spatial_data[:, 0]
        y = spatial_data[:, 1]
        # if vessel_dict[i] is -1:
        #     print('Inverting the interpolation points in vessel_%d in monotonic order' % i)
        #     x = x[::-1]
        #     y = y[::-1]
        #     try:
        #         spline_ = UnivariateSpline(x, y, k=2, s=0)
        #     except:
        #         spline_ = interp1d(x, y)
        #     XX[i] = np.linspace(x[0], x[-1], no_sampling_points)
        #     YY[i] = spline_(XX[i])
        #
        #     XX[i] = XX[i][::-1]
        #     YY[i] = YY[i][::-1]
        # else:
        #     spline_ = UnivariateSpline(x, y, k=2, s=0)
        spline_ = interp1d(x, y)
        XX[i] = np.linspace(x[0], x[-1], no_sampling_points)
        YY[i] = spline_(XX[i])


    n = 0
    no_of_points = 0
    no_of_blocks = len(vessel_dict.keys())
    for j in range(0, clms, 25):

        block_index = 0
        multiblock = vtk.vtkMultiBlockDataSet()
        multiblock.SetNumberOfBlocks(no_of_blocks)

        for mb in vessel_dict.keys():

            no_vtk_points = XX[mb].shape[0]

            points = vtk.vtkPoints()
            segment = vtk.vtkPolyLine()
            lines = vtk.vtkCellArray()

            radius = vtk.vtkDoubleArray()
            radius.SetName("radius")
            radius.SetNumberOfComponents(1)
            radius.SetNumberOfTuples(no_vtk_points)

            pressure = vtk.vtkDoubleArray()
            pressure.SetName("pressure")
            pressure.SetNumberOfComponents(1)
            pressure.SetNumberOfTuples(no_vtk_points)

            flow = vtk.vtkDoubleArray()
            flow.SetName("flow")
            flow.SetNumberOfComponents(1)
            flow.SetNumberOfTuples(no_vtk_points)

            velocity = vtk.vtkDoubleArray()
            velocity.SetName("velocity")
            velocity.SetNumberOfComponents(1)
            velocity.SetNumberOfTuples(no_vtk_points)

            points.SetNumberOfPoints(no_vtk_points)
            segment.GetPointIds().SetNumberOfIds(no_vtk_points)
            for i in range(no_vtk_points):
                points.InsertPoint(i, XX[mb][i], YY[mb][i], 0.)
                segment.GetPointIds().SetId(i, i)

                radius.InsertTuple1(i, np.sqrt(A[mb][i, j] / np.pi))
                pressure.InsertTuple1(i, p[mb][i, j])
                flow.InsertTuple1(i, q[mb][i, j])
                velocity.InsertTuple1(i, u[mb][i, j])

            lines.InsertNextCell(segment)

            profileData = vtk.vtkPolyData()
            profileData.SetPoints(points)
            profileData.SetLines(lines)
            profileData.GetPointData().AddArray(radius)
            profileData.GetPointData().AddArray(pressure)
            profileData.GetPointData().AddArray(flow)
            profileData.GetPointData().AddArray(velocity)
            profileData.GetPointData().SetActiveScalars("radius")

            # Add thickness to the resulting line.
            profileTubes = vtk.vtkTubeFilter()
            profileTubes.SetNumberOfSides(20)
            profileTubes.SetInputData(profileData)
            profileTubes.SetInputArrayToProcess(0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "radius")
            # profileTubes.SetRadius(.01)
            # Vary tube thickness with scalar
            profileTubes.SetRadiusFactor(2)
            profileTubes.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
            # profileTubes.Update()
            multiblock.SetBlock(block_index, profileData)
            multiblock.GetMetaData(block_index).Set(vtk.vtkCompositeDataSet.NAME(), 'Vessel_%d' % mb)

            block_index += 1


        # print(type(profileTubes.GetOutputPort()))

        multiBlockWriter = vtk.vtkXMLMultiBlockDataWriter()
        file_ext = multiBlockWriter.GetDefaultFileExtension()
        ofilename = './' + ovisfile + '_%02d.' % (n)
        multiBlockWriter.SetFileName(ofilename + file_ext)
        multiBlockWriter.SetInputData(multiblock)
        multiBlockWriter.Update()
        multiBlockWriter.UpdateInformation()
        multiBlockWriter.Write()

        n += 1

    return STATUS_OK

def vpwtkResPolyDataFileWriter(ifilename, vessel_dict):

    # sampling frequency
    fr = 1  # kHz
    sampling_period = 0.001
    no_points = 1.0 / 0.001

    # results file
    myodbf = ExtractUVectors(ifilename)

    A = {}
    p = {}
    q = {}
    u = {}
    X = {}
    t = None
    XX = {}
    YY = {}
    for i in vessel_dict.keys():
        A[i], q[i], p[i], u[i] = myodbf.getUVector(vessel_no=i, cycle=4, no_points=no_points)
        t = myodbf.meshgrid_T
        X = myodbf.meshgrid_X

        rws, clms = X.shape
        # print(vtk.vtkVersion().GetVTKVersion())
        # A_b, q_b, p_b, u_b = myodbf.getUVector(vessel_no=54, cycle=4, no_points=no_points)
        # T_i = myodbf.meshgrid_T
        # X_i = myodbf.meshgrid_X
        nodes = X[:, 0]

        num_points = nodes.shape[0]
        spatial_data = np.loadtxt('./data/' + str(i) + 'vessel_points.dat', delimiter=',')
        x = spatial_data[:, 0]
        y = spatial_data[:, 1]
        if vessel_dict[i] is -1:
            x = x[::-1]
            y = y[::-1]
        # x = np.array([1., 20., 30., 40., 50., 60.])
        # y = np.array([0., 0., 10., 10., 0., 0.])
        spline_ = UnivariateSpline(x, y, k=2, s=0)

        XX[i] = np.linspace(x[0], x[-1], num_points)
        YY[i] = spline_(XX[i])

        if vessel_dict[i] is -1:
            XX[i] = XX[i][::-1]
            YY[i] = YY[i][::-1]
    #    x = np.array([123.220, 137.205, 148.167, 151.568, 155.726,
    #                  156.104, 156.104])*10
    #    y = np.array([207.509, 193.146, 176.893, 156.860, 137.961,
    #                  121.708, 113.015])*10
    #    spline_ = UnivariateSpline(x, y, k=2, s=0)
    #    XX = np.linspace(x[0], x[-1], num_points)
    #    YY = spline_(XX)
        # name_A = 'A'
        # name_q = 'q'
        # name_p = 'p'
        # name_u = 'u'
        # name_t = 't'
        # name_x = 'x'
        # kwards = {name_A: A_b, name_q: q_b, name_p: p_b, name_u: u_b, name_t: T_i, name_x: X_i}
        # filename = './Vessel_%2d.dat' % vessel_no
        # np.savez(filename, **kwards)

        num_points = nodes.shape[0]
    # num_points = 10
    print(num_points)
    n = 0
    no_of_points = 0
    for i in vessel_dict.keys():
        no_of_points += XX[i].shape[0]
    no_of_polylines = len(vessel_dict.keys())

    for j in range(0, clms, 25):

        radius = vtk.vtkDoubleArray()
        radius.SetName("radius")
        radius.SetNumberOfComponents(1)
        radius.SetNumberOfTuples(no_of_points)

        pressure = vtk.vtkDoubleArray()
        pressure.SetName("pressure")
        pressure.SetNumberOfComponents(1)
        pressure.SetNumberOfTuples(no_of_points)

        flow = vtk.vtkDoubleArray()
        flow.SetName("flow")
        flow.SetNumberOfComponents(1)
        flow.SetNumberOfTuples(no_of_points)

        velocity = vtk.vtkDoubleArray()
        velocity.SetName("velocity")
        velocity.SetNumberOfComponents(1)
        velocity.SetNumberOfTuples(no_of_points)

        points = vtk.vtkPoints()
        points.SetNumberOfPoints(num_points)
        id = 0
        for k in vessel_dict.keys():
            for i in range(num_points):
                points.InsertPoint(id, XX[k][i], YY[k][i], 0.)
                id += 1

        id = 0
        # Create the polyline.
        lines = vtk.vtkCellArray()
        for k in vessel_dict.keys():
            segment = vtk.vtkPolyLine()
            segment.GetPointIds().SetNumberOfIds(num_points)
            for i in range(num_points):
                segment.GetPointIds().SetId(i, id)

                radius.InsertTuple1(id, np.sqrt(A[k][i, j] / np.pi))
                pressure.InsertTuple1(id, p[k][i, j])
                flow.InsertTuple1(id, q[k][i, j])
                velocity.InsertTuple1(i, u[k][i, j])
                id += 1
            lines.InsertNextCell(segment)


        # # Create the polyline.
        # lines = vtk.vtkCellArray()
        # lines.InsertNextCell(segment)

        profileData = vtk.vtkPolyData()
        profileData.SetPoints(points)
        profileData.SetLines(lines)
        profileData.GetPointData().AddArray(radius)
        profileData.GetPointData().AddArray(pressure)
        profileData.GetPointData().AddArray(flow)
        profileData.GetPointData().AddArray(velocity)
        profileData.GetPointData().SetActiveScalars("radius")

        # define unstructured grid
        # aPolyGrid = vtk.vtkUnstructuredGrid()
        # aPolyGrid.Allocate(1, 1)
        # aPolyGrid.InsertNextCell(segment.GetCellType(), segment.GetPointIds())
        # aPolyGrid.SetPoints(points)
        # aPolyGrid.GetPointData().AddArray(radius)
        # aPolyGrid.GetPointData().SetActiveScalars("radius")

        # Add thickness to the resulting line.
        profileTubes = vtk.vtkTubeFilter()
        profileTubes.SetNumberOfSides(20)
        profileTubes.SetInputData(profileData)
        profileTubes.SetInputArrayToProcess(0,0,0, vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "radius")
        # profileTubes.SetRadius(.01)
        # Vary tube thickness with scalar
        profileTubes.SetRadiusFactor(2)
        profileTubes.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
        # profileTubes.Update()

        print(type(profileTubes.GetOutputPort()))
        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetFileName('tube_%02d.vtp' % n)
        writer.SetInputConnection(profileTubes.GetOutputPort())
        writer.Write()

        n += 1
    # ------------------------------------------ #
#    drange = pressure.GetRange()
#
#    #region LOOKUP TABLE & SCALARBOX
#    # add look up table
#    lookupTable = vtk.vtkLookupTable()
#    lookupTable.SetNumberOfColors(20)
#    lookupTable.SetHueRange(0.667, 0)
#    lookupTable.SetTableRange(drange)
#    lookupTable.Build()
#
#    # add ScalarBar Actor and Set Properties
#    activeScalarBar = vtk.vtkScalarBarActor()
#    activeScalarBar.SetLookupTable(lookupTable)
#    activeScalarBar.SetNumberOfLabels(3)
#    activeScalarBar.GetPosition2Coordinate().SetCoordinateSystemToNormalizedViewport()
#    activeScalarBar.SetHeight(0.4)
#    activeScalarBar.SetWidth(0.1)
#    activeScalarBar.SetLabelFormat("%.6f")
#    activeScalarBar.SetTitle("pressure")
#    activeScalarBar.SetTextPositionToPrecedeScalarBar()
#    activeScalarBar.UseOpacityOff()
#    activeScalarBar.VisibilityOn()
#
#    myText = vtk.vtkTextProperty()
#    myText = activeScalarBar.GetLabelTextProperty()
#    myText.SetFontSize(8)
#    myText.ItalicOff()
#    myText.BoldOff()
#    myText.SetColor(0.0, 0.0, 0.0)
#    myText.SetFontFamilyToTimes()
#    myText.ShadowOff()
#
#    activeScalarBar.SetTitleTextProperty(myText)
#    activeScalarBar.SetLabelTextProperty(myText)
#    #endregion
#    # ------------------------------------------ #
#
#
#    profileMapper = vtk.vtkPolyDataMapper()
#    profileMapper.SetInputConnection(profileTubes.GetOutputPort())
#    # profileMapper.SetScalarRange(0,t)
#    #Set this to Off to turn off color variation with scalar
#    profileMapper.ScalarVisibilityOn()
#    profileMapper.SetLookupTable(lookupTable)
#    # profileMapper.SetScalarModeToUsePointFieldData()
#    profileMapper.SetScalarRange(profileData.GetScalarRange())
#
#    profile = vtk.vtkActor()
#    profile.SetMapper(profileMapper)
#    # profile.GetProperty().SetSpecular(.3)
#    # profile.GetProperty().SetSpecularPower(30)
#
#    # set the mapper
#    aTetraMapper = vtk.vtkPolyDataMapper()
#    aTetraMapper.SetInputData(profileData)
#    aTetraMapper.SetLookupTable(lookupTable)
#    aTetraMapper.SetScalarRange(profileData.GetScalarRange())
#
#    # set the actor
#    aTetraActor = vtk.vtkActor()
#    aTetraActor.SetMapper(aTetraMapper)
#    # aTetraActor.AddPosition(4, 0, 0)
#    # aTetraActor.GetProperty().SetDiffuseColor(0, 1, 0)
#
#    # ------------------------------------------ #
#    # axes actor
#    axesTriad = vtk.vtkAxesActor()
#    axesTriad.AddPosition(0.0, 0.0, 0.0)
#    axesTriad.SetShaftTypeToCylinder()
#    axesTriad.SetXAxisLabelText("x")
#    axesTriad.SetYAxisLabelText("y")
#    axesTriad.SetZAxisLabelText("z")
#    axesTriad.SetTotalLength(1.5, 1.5, 1.5)
#
#    # properties for the axis actor
#    textXLabels = vtk.vtkTextProperty()
#    textYLabels = vtk.vtkTextProperty()
#    textZLabels = vtk.vtkTextProperty()
#
#    textXLabels.SetFontFamilyToTimes()
#    textYLabels.SetFontFamilyToTimes()
#    textZLabels.SetFontFamilyToTimes()
#    textXLabels.SetFontSize(6)
#    textYLabels.SetFontSize(6)
#    textZLabels.SetFontSize(6)
#
#    axesTriad.GetXAxisCaptionActor2D().SetCaptionTextProperty(textXLabels)
#    axesTriad.GetYAxisCaptionActor2D().SetCaptionTextProperty(textYLabels)
#    axesTriad.GetZAxisCaptionActor2D().SetCaptionTextProperty(textZLabels)
#    axesTriad.GetXAxisCaptionActor2D().GetCaptionTextProperty().ShadowOff()
#    axesTriad.GetYAxisCaptionActor2D().GetCaptionTextProperty().ShadowOff()
#    axesTriad.GetZAxisCaptionActor2D().GetCaptionTextProperty().ShadowOff()
#
#    axesWidget = vtk.vtkOrientationMarkerWidget()
#    # place it at lower left corner
#    #axesWidget.SetViewport(0.0, 0.0, 0.3, 0.3);
#    axesWidget.SetOrientationMarker(axesTriad)
#    axesWidget.SetInteractor(iren)
#    axesWidget.EnabledOn()
#    axesWidget.InteractiveOff()
#    axesWidget.KeyPressActivationOff()
#    # ------------------------------------------ #
#
#
#    ren.AddActor(aTetraActor)
#    ren.AddActor(profile)
#    ren.AddActor2D(activeScalarBar)
#
#
#    ren.ResetCamera()
#    # ren.GetActiveCamera().Azimuth(30)
#    # ren.GetActiveCamera().Elevation(20)
#    # ren.GetActiveCamera().Dolly(2.8)
#    # ren.ResetCameraClippingRange()
#
#    # Render the scene and start interaction.
#    iren.Initialize()
#    renWin.Render()
#    axesWidget.On()
#    iren.Start()
#    iren.Disable()

    return STATUS_OK

def main(ifilename, ovisfile):

    # VESSELS = {0: 1, 1: -1, 2: 1, 3: -1, 4: 1, 5: 1, 6: -1, 7: -1,
    #            8: -1, 9: -1, 10: 1, 11: -1, 12: -1, 13: -1, 14: -1,
    #            15: 1, 16: 1, 17: 1, 18: 1, 19: -1, 20: 1, 21: 1, 22: -1, 23: 1, 24: 1, 25: 1, 26: 1,
    #            27: 1, 28: -1, 29: 1, 30: 1, 31: 1, 32: -1, 33: -1, 34: 1, 35: -1, 36: -1, 37: -1, 38: 1,
    #            39: -1, 40: -1, 41: -1, 42: -1, 43: -1, 44: -1, 45: -1, 46: -1, 47: 1, 48: -1, 49: 1,
    #            50: -1, 51: -1, 52: -1, 53: 1, 54: -1, 55: -1, 56: 1, 57: -1, 58: -1, 59: 1, 60: -1,
    #            61: 1, 62: -1, 63: -1, 64: 1, 65: 1, 66: 1, 67: 1, 68: 1, 69: -1, 70: 1, 71: -1,
    #            72: 1, 73: 1, 74: -1, 75: -1, 76: -1}

    # for hand
    VESSELS = {0: -1, 1: -1, 2: -1, 3: 1, 4: -1, 5: -1, 6: -1}
    vessel_map = {0: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13}
    # vessel_map = {i: i for i in range(77)}

    # res = vpwtkResPolyDataFileWriter(ifilename, VESSELS)
    res = vpwtkResMultiBlockFileWriter(ifilename, VESSELS, vessel_map, ovisfile)

    return res

if __name__ == '__main__':
    import sys
    parser = argprs.ArgumentParser(description='Write multiblock vtk files for visualisation')
    parser.add_argument('-iresfile', help='input res (.npz) file from pylsewave')
    parser.add_argument('-ovisfile', help='Output visualisation file')
    args = parser.parse_args()
    print(args)
    if (args.iresfile is None) or (args.ovisfile is None):
        print('File should be exected as:\n' + sys.argv[0] + " -resfile <resfile> -ovisfile <visfile>")
        print(STATUS_ERROR)
    else:
        status = main(args.iresfile, args.ovisfile)
        print(status)
