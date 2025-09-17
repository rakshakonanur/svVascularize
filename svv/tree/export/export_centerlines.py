import numpy
import pyvista
from copy import deepcopy
from scipy.interpolate import splprep, splev
import os

def get_longest_path(data, seed_edge):
    dig = True
    temp_edges = [seed_edge]
    while dig:
        keep_digging = []
        for edge in temp_edges:
            if not numpy.isnan(data[edge, 15]):
                temp_edges.extend([int(data[edge, 15])])
                if not numpy.isnan(data[edge, 16]):
                    temp_edges.extend([int(data[edge, 16])])
                temp_edges.remove(edge)
                keep_digging.append(True)
            else:
                keep_digging.append(False)
        dig = any(keep_digging)
    if len(temp_edges) == 1:
        return temp_edges
    edge_depths = []
    for edge in temp_edges:
        edge_depths.append(data[edge, 26])
    max_depth = max(edge_depths)
    max_edge_depths = [i for i, j in enumerate(edge_depths) if j == max_depth]
    paths = [[temp_edges[i]] for i in max_edge_depths]
    path_lengths = [data[i[0], 20] for i in paths]
    retrace = [True]*len(paths)
    while any(retrace):
        for i, path in enumerate(paths):
            if retrace[i]:
                path.insert(0, int(data[path[0], 17]))
                path_lengths[i] += data[path[0], 20]
                if paths[i][0] == seed_edge:
                    retrace[i] = False
    return paths[path_lengths.index(max(path_lengths))]


def get_alternate_path(data, seed_edge, reference=None):
    if reference is None:
        reference = get_longest_path(data, seed_edge)
    else:
        pass
    seed_edge_idx = reference.index(seed_edge)
    if seed_edge_idx == len(reference)-1:
        print('Seed edge is terminal and no alternative is possible. \n Computation finished.')
        return None
    else:
        children = [int(data[seed_edge, 15]), int(data[seed_edge, 16])]
        if children[0] not in reference:
            alternate_path = get_longest_path(data, children[0])
        else:
            alternate_path = get_longest_path(data, children[1])
    alternate_path.insert(0, seed_edge)
    return alternate_path


def get_branches(data):
    branches = []
    seed_edge = 0
    path = get_longest_path(data, seed_edge)
    branches.append(path)
    upcoming_evaluations = []
    upcoming_evaluations.extend(path[:-1])
    counter = [len(path[:-1])]
    idx = 0
    while len(upcoming_evaluations) > 0:
        if not numpy.isnan(data[upcoming_evaluations[-1], 15]) and not numpy.isnan(data[upcoming_evaluations[-1], 16]):
            pass
        else:
            upcoming_evaluations.pop(-1)
            counter[idx] -= 1
            if counter[idx] == 0:
                counter[idx] = None
                for i in reversed(range(len(counter))):
                    if counter[i] is not None:
                        idx = i
                        break
            continue
        path = get_alternate_path(data, upcoming_evaluations.pop(-1), reference=branches[idx])
        counter[idx] -= 1
        if counter[idx] == 0:
            counter[idx] = None
            for i in reversed(range(len(counter))):
                if counter[i] is not None:
                    idx = i
                    break
        branches.append(path)
        if len(path) > 2:
            upcoming_evaluations.extend(path[1:-1])
            counter.append(len(path[1:-1]))
            idx = len(counter) - 1
        else:
            counter.append(None)
    return branches


def get_points(data, branches):
    path_points = []
    primed = False
    for path in branches:
        branch_points = []
        for edge in reversed(path):
            if edge == path[0] and primed:
                branch_points.insert(0, data[edge, 3:6].tolist())
            elif edge == path[0] and edge == 0 and not primed:
                branch_points.insert(0, data[edge, 3:6].tolist())
                three_fourths = data[edge, 0:3]*(1/4) + data[edge, 3:6]*(3/4)
                branch_points.insert(0, three_fourths.tolist())
                mid_point = (data[edge, 0:3] + data[edge, 3:6])/2
                branch_points.insert(0, mid_point.tolist())
                one_fourth = data[edge, 0:3]*(3/4) + data[edge, 3:6]*(1/4)
                branch_points.insert(0, one_fourth.tolist())
                branch_points.insert(0, data[edge, 0:3].tolist())
                primed = True
            elif len(branch_points) == 0:
                branch_points.insert(0, data[edge, 3:6].tolist())
                three_fourths = data[edge, 0:3]*(1/4) + data[edge, 3:6]*(3/4)
                branch_points.insert(0, three_fourths.tolist())
                mid_point = (data[edge, 0:3] + data[edge, 3:6])/2
                branch_points.insert(0, mid_point.tolist())
                one_fourth = data[edge, 0:3]*(3/4) + data[edge, 3:6]*(1/4)
                branch_points.insert(0, one_fourth.tolist())
            else:
                branch_points.insert(0, data[edge, 3:6].tolist())
                three_fourths = data[edge, 0:3]*(1/4) + data[edge, 3:6]*(3/4)
                branch_points.insert(0, three_fourths.tolist())
                mid_point = (data[edge, 0:3] + data[edge, 3:6])/2
                branch_points.insert(0, mid_point.tolist())
                one_fourth = data[edge, 0:3]*(3/4) + data[edge, 3:6]*(1/4)
                branch_points.insert(0, one_fourth.tolist())
        path_points.append(branch_points)
    return path_points


def get_radii(data, branches):
    path_radii = []
    primed = False
    for path in branches:
        branch_radii = []
        for edge in reversed(path):
            if edge == path[0] and primed:
                branch_radii.insert(0, data[path[1], 21])
            elif edge == path[0] and edge == 0 and not primed:
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                primed = True
            elif len(branch_radii) == 0:
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
            else:
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
                branch_radii.insert(0, data[edge, 21])
        path_radii.append(branch_radii)
    return path_radii


def get_normals(data, branches):
    path_normals = []
    primed = False
    for path in branches:
        branch_normals = []
        for edge in reversed(path):
            if edge == path[0] and primed:
                branch_normals.insert(0, data[path[1], 12:15].tolist())
            elif edge == path[0] and edge == 0 and not primed:
                vector_1 = data[edge, 12:15]
                mid_vector = (vector_1 + vector_2)/2
                branch_normals.insert(0, mid_vector.tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                primed = True
            elif len(branch_normals) == 0:
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                vector_2 = data[edge, 12:15]
            else:
                vector_1 = data[edge, 12:15]
                mid_vector = (vector_1+vector_2)/2
                branch_normals.insert(0, mid_vector.tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                branch_normals.insert(0, data[edge, 12:15].tolist())
                vector_2 = data[edge, 12:15]
        path_normals.append(branch_normals)
    return path_normals


def get_interpolated_sv_data(data):
    branches = get_branches(data)
    points = get_points(data, branches)
    radii = get_radii(data, branches)
    normals = get_normals(data, branches)
    path_frames = []
    for idx in range(len(branches)):
        frames = []
        for jdx in range(len(points[idx])):
            frame = []
            frame.extend(points[idx][jdx])
            frame.append(radii[idx][jdx])
            frame.extend(normals[idx][jdx])
            frames.append(frame)
        path_frames.append(frames)
    interp_xyz = []
    interp_r = []
    interp_n = []
    interp_xyzr = []
    for idx in range(len(branches)):
        p = numpy.array(points[idx]).T
        r = numpy.array(radii[idx]).T
        n = numpy.array(normals[idx]).T
        if len(points[idx]) == 2:
            interp_xyz.append(splprep(p, k=1, s=0))
            rr = numpy.vstack((interp_xyz[-1][1], r))
            interp_r.append(splprep(rr, k=1, s=0))
            xyzr = numpy.vstack((p, r))
            interp_xyzr.append(splprep(xyzr, k=1, s=0))
            #interp_n.append(splprep(n, k=1, s=0))
        elif len(points[idx]) == 3:
            interp_xyz.append(splprep(p, k=2, s=0))
            rr = numpy.vstack((interp_xyz[-1][1], r))
            interp_r.append(splprep(rr, k=1, s=0))
            xyzr = numpy.vstack((p, r))
            interp_xyzr.append(splprep(xyzr, k=2, s=0))
            #interp_n.append(splprep(n, k=2, s=0))
        else:
            interp_xyz.append(splprep(p, s=0))
            rr = numpy.vstack((interp_xyz[-1][1], r))
            interp_r.append(splprep(rr, k=1, s=0))
            xyzr = numpy.vstack((p, r))
            interp_xyzr.append(splprep(xyzr, s=0))
            #interp_n.append(splprep(n, s=0))
    return interp_xyz, interp_r, interp_n, path_frames, branches, interp_xyzr


def build_centerlines(tree, outdir, points_per_unit_length=5000, distal_pressure=0, resistance_split=(1,0), steady=True):
    """
    Export centerline to a file.
    """
    data = deepcopy(tree.data)
    interp_xyz, interp_r, interp_n, path_frames, branches, interp_xyzr = get_interpolated_sv_data(data)

    def make_points(x, y, z):
        """Helper to make XYZ points"""
        return numpy.column_stack((x, y, z))

    def lines_from_points(points):
        """Given an array of points, make a line set"""
        poly = pyvista.PolyData()
        poly.points = points
        cells = numpy.full((len(points) - 1, 3), 2, dtype=numpy.int_)
        cells[:, 1] = numpy.arange(0, len(points) - 1, dtype=numpy.int_)
        cells[:, 2] = numpy.arange(1, len(points), dtype=numpy.int_)
        poly.lines = cells
        return poly

    polys = []
    total_outlet_area = 0.0
    for ind, spline in enumerate(interp_xyzr):
        n = numpy.linspace(0, 1, 1000)
        spline_data = splev(n, spline[0])
        spline_data_normal = splev(n, spline[0], der=1)
        points = make_points(spline_data[0], spline_data[1], spline_data[2])
        dist = numpy.sum(numpy.linalg.norm(numpy.diff(points, axis=0), axis=1))
        # num_points = 2 + int(dist*points_per_unit_length)
        num_points = 1000  #Raksha- toggle for num points depending on length or constant
        n = numpy.linspace(0, 1, num_points)
        spline_data = splev(n, spline[0])
        spline_r_data = numpy.array(spline_data[3]).flatten()
        spline_data_normal = splev(n, spline[0], der=1)
        points = make_points(spline_data[0], spline_data[1], spline_data[2])
        normal = make_points(spline_data_normal[0], spline_data_normal[1], spline_data_normal[2])
        normal = normal / numpy.linalg.norm(normal, axis=1).reshape(-1, 1)
        poly_line = lines_from_points(points)
        poly_line['VesselId'] = numpy.ones(num_points, dtype=int)*ind
        poly_line['MaximumInscribedSphereRadius'] = spline_r_data
        poly_line['CenterlineSectionArea'] = numpy.pi * spline_r_data ** 2
        poly_line['BifurcationIdTmp'] = numpy.ones(num_points, dtype=int) * -1
        poly_line['BifurcationId'] = numpy.ones(num_points, dtype=int) * -1
        poly_line['BranchId'] = numpy.ones(num_points, dtype=int) * -1
        poly_line.point_data.set_array(normal, 'CenterlineSectionNormal')
        polys.append(poly_line)
        total_outlet_area += poly_line['CenterlineSectionArea'][-1]

    # # OTHER METHOD: FROM SVCCO
    # num_points = 1000
    # polys = []
    # total_outlet_area = 0
    # for ind in range(len(interp_xyz)): #(interp_xyzr):
    #     n = numpy.linspace(0,1,num_points)
    #     #spline_data = splev(n,spline[0])
    #     #spline_data_normal = splev(n,spline[0],der=1)
    #     spline_data = splev(n,interp_xyz[ind][0])
    #     spline_data_normal = splev(n,interp_xyz[ind][0],der=1)
    #     _,spline_r_data   = splev(n,interp_r[ind][0])
    #     spline_r_data = numpy.array(spline_r_data).flatten()
    #     points = make_points(spline_data[0],spline_data[1],spline_data[2])
    #     normal = make_points(spline_data_normal[0],spline_data_normal[1],spline_data_normal[2])
    #     normal = normal/numpy.linalg.norm(normal,axis=1).reshape(-1,1)
    #     poly_line = lines_from_points(points)
    #     poly_line['VesselId'] = numpy.ones(num_points,dtype=int)*ind
    #     poly_line['MaximumInscribedSphereRadius'] = spline_r_data #spline_data[3]
    #     poly_line['CenterlineSectionArea'] = numpy.pi*spline_r_data**2
    #     poly_line['BifurcationIdTmp'] = numpy.ones(num_points,dtype=int)*-1
    #     poly_line['BifurcationId'] = numpy.ones(num_points,dtype=int)*-1
    #     poly_line['BranchId'] = numpy.ones(num_points,dtype=int)*-1
    #     poly_line.point_data.set_array(normal,'CenterlineSectionNormal')
    #     polys.append(poly_line)
    #     total_outlet_area += poly_line['CenterlineSectionArea'][-1]

    for ind in range(len(polys)):
        cent_ids = numpy.zeros((polys[ind].n_points, len(polys)), dtype=int)
        polys[ind].point_data.set_array(cent_ids, 'CenterlineId')
        polys[ind].point_data['CenterlineId'][:, ind] = 1

    bifurcation_point_ids = []  # polys ind index, polys jnd index, polys jnd point index
    for ind in range(1, len(polys)):
        current_closest_dist = numpy.inf
        current_closest_branch = None
        current_closest_pt_id = None
        for jnd in range(len(polys)):
            if jnd == ind:
                continue
            closest_pt_id = polys[jnd].find_closest_point(polys[ind].points[0])
            closest_point = polys[jnd].points[closest_pt_id]
            closest_dist_tmp = numpy.linalg.norm(polys[ind].points[0] - closest_point)
            if closest_dist_tmp < current_closest_dist:
                current_closest_branch = jnd
                current_closest_dist = closest_dist_tmp
                current_closest_pt_id = closest_pt_id
                current_closest_point = closest_point
        bifurcation_point_ids.append([ind, current_closest_branch, current_closest_pt_id, current_closest_point])
        polys[current_closest_branch].point_data['CenterlineId'][0:current_closest_pt_id+1, ind] = 1
        while current_closest_branch != 0:
            # print("current_closest_branch:", current_closest_branch)
            # print("current branch id:", ind)
            # print("Bifurcation between branch {} and branch {} at point id {} on branch {}".format(ind, current_closest_branch, current_closest_pt_id, current_closest_branch))
            closest_branch = current_closest_branch
            current_closest_dist = numpy.inf
            current_closest_branch = None
            current_closest_pt_id = None
            for jnd in range(len(polys)):
                # print(jnd, closest_branch)
                if jnd == closest_branch:
                    continue
                closest_pt_id = polys[jnd].find_closest_point(polys[closest_branch].points[0])
                closest_point = polys[jnd].points[closest_pt_id]
                closest_dist_tmp = numpy.linalg.norm(polys[closest_branch].points[0] - closest_point)
                # print(closest_branch, jnd, closest_pt_id)
                # print(closest_dist_tmp-current_closest_dist)
                if closest_dist_tmp < current_closest_dist:  
                # EPS = 1e-4 # or maybe 1e-6 depending on your units: Raksha
                # if closest_dist_tmp < current_closest_dist - EPS:
                    current_closest_branch = jnd
                    # print(closest_dist_tmp, current_closest_dist)
                    current_closest_dist = closest_dist_tmp
                    current_closest_pt_id = closest_pt_id
                    current_closest_point = closest_point
            polys[current_closest_branch].point_data['CenterlineId'][0:current_closest_pt_id+1, ind] = 1



    # Determine Branch Temp Ids (CORRECT)
    branch_tmp_count = 0
    for ind in range(len(polys)):
        tmp_split = []
        for bif in bifurcation_point_ids:
            if bif[1] == ind:
                tmp_split.append(bif[2])
        tmp_split.sort()
        tmp_split.insert(0, 0)
        tmp_split.append(None)
        branch_tmp_ids = numpy.zeros(polys[ind].points.shape[0], dtype=int)
        for i in range(1, len(tmp_split)):
            branch_tmp_ids[tmp_split[i - 1]:tmp_split[i]] = branch_tmp_count
            branch_tmp_count += 1
        polys[ind].point_data['BranchIdTmp'] = branch_tmp_ids

    # Determine BifurcationTempIds (1: bifucation point, 2: surrounding points)
    for ind in range(len(polys)):
        for id, bif in enumerate(bifurcation_point_ids):
            if bif[1] == ind:
                rad = polys[ind].point_data['MaximumInscribedSphereRadius'][bif[2]]
                pt = bif[3]
                # parent_surrounding_point_ids = np.argwhere(np.linalg.norm(polys[ind].points[:-4,:] - pt,axis=1)<rad).flatten().tolist()
                parent_surrounding_point_ids = [bif[2]]
                if len(parent_surrounding_point_ids) < 3:
                    if not any(numpy.array(parent_surrounding_point_ids) < bif[2]):
                        if bif[2] > 0:
                            parent_surrounding_point_ids.append(bif[2] - 1)
                    if not any(numpy.array(parent_surrounding_point_ids) > bif[2]):
                        if bif[2] < polys[ind].points.shape[0] - 1:
                            parent_surrounding_point_ids.append(bif[2] + 1)
                # daughter_surrounding_point_ids = np.argwhere(np.linalg.norm(polys[bif[0]].points[:-4,:] - pt,axis=1)<rad).flatten().tolist()
                daughter_surrounding_point_ids = []
                if len(daughter_surrounding_point_ids) < 2:
                    if 0 not in daughter_surrounding_point_ids:
                        daughter_surrounding_point_ids.append(0)
                    if 1 not in daughter_surrounding_point_ids:
                        daughter_surrounding_point_ids.append(1)
                parent_surrounding_point_ids.pop(parent_surrounding_point_ids.index(bif[2]))
                parent_surrounding_point_ids = numpy.array(parent_surrounding_point_ids)
                daughter_surrounding_point_ids = numpy.array(daughter_surrounding_point_ids)
                polys[ind].point_data['BifurcationIdTmp'][parent_surrounding_point_ids] = 2
                polys[ind].point_data['BifurcationIdTmp'][bif[2]] = 1
                polys[bif[0]].point_data['BifurcationIdTmp'][daughter_surrounding_point_ids] = 2
                polys[ind].point_data['BifurcationId'][parent_surrounding_point_ids] = id
                polys[ind].point_data['BifurcationId'][bif[2]] = id
                polys[bif[0]].point_data['BifurcationId'][daughter_surrounding_point_ids] = id

    branch_id_count = 0
    for ind in range(len(polys)):
        new = True
        for jnd in range(polys[ind].n_points):
            if polys[ind].point_data['BifurcationId'][jnd] < 0:
                polys[ind].point_data['BranchId'][jnd] = branch_id_count
                new = False
            elif not new and polys[ind].point_data['BifurcationId'][jnd] >= 0 and \
                    polys[ind].point_data['BifurcationId'][jnd - 1] < 0:  # fix this line for jnd < 0
                branch_id_count += 1
        branch_id_count += 1

    # Set Path Values for Branches and Bifurcations also obtain outlet branches
    outlets = []
    for ind in range(len(polys)):
        branch_ids = list(set(polys[ind].point_data['BranchId'].tolist()))
        outlets.append(max(branch_ids))
        branch_ids.sort()
        path_init = numpy.zeros(polys[ind].points.shape[0])
        polys[ind].point_data['Path'] = path_init
        if branch_ids[0] == -1:
            branch_ids = branch_ids[1:]
        for b_idx in branch_ids:
            poly_pt_ids = numpy.argwhere(polys[ind].point_data['BranchId'] == b_idx).flatten()
            poly_pt_path = numpy.cumsum(
                numpy.insert(numpy.linalg.norm(numpy.diff(polys[ind].points[poly_pt_ids], axis=0), axis=1), 0, 0))
            polys[ind].point_data['Path'][poly_pt_ids] = poly_pt_path
        bif_ids = list(set(polys[ind].point_data['BifurcationId'].tolist()))
        bif_ids.sort()
        if bif_ids[0] == -1:
            bif_ids = bif_ids[1:]
        for bif_idx in bif_ids:
            poly_pt_ids = numpy.argwhere(polys[ind].point_data['BifurcationId'] == bif_idx).flatten()
            poly_pt_path = numpy.cumsum(
                numpy.insert(numpy.linalg.norm(numpy.diff(polys[ind].points[poly_pt_ids], axis=0), axis=1), 0, 0))
            polys[ind].point_data['Path'][poly_pt_ids] = poly_pt_path

    # Set Point Ids
    Global_node_count = 0
    branch_starts = []
    for ind in range(len(polys)):
        GlobalNodeId = list(range(Global_node_count, Global_node_count + polys[ind].n_points))
        Global_node_count = GlobalNodeId[-1] + 1
        if ind < len(polys):
            branch_starts.append(Global_node_count)
        GlobalNodeId = numpy.array(GlobalNodeId)
        polys[ind].point_data['GlobalNodeId'] = GlobalNodeId

    # Merge and Connect Lines
    centerlines_all = polys[0]
    for ind in range(1, len(polys)):
        closest_pt_id = centerlines_all.find_closest_point(polys[ind].points[0])
        closest_point_original = deepcopy(centerlines_all.points[closest_pt_id])
        centerlines_all = centerlines_all.merge(polys[ind], merge_points=False)
        closest_next_id = centerlines_all.find_closest_point(polys[ind].points[0])
        closest_pt_id = centerlines_all.find_closest_point(closest_point_original)
        new_line = [2, closest_pt_id, closest_next_id]
        centerlines_all.lines = numpy.hstack((centerlines_all.lines, numpy.array(new_line)))

    # Generate Outlet Face File: Raksha Added
    outlet_file = open(outdir+os.sep+'outlets',"w+")
    for i in range(len(polys)):
        outlet_file.write("cap_{}\n".format(i+1))
    outlet_file.close()

    # Genrate Boundary Condition File (need to create real boundary conditions)
    total_resistance = (tree.parameters.terminal_pressure - 1333*distal_pressure)/tree.data[0,22]
    #split = (1,0)
    rcrt_file = open(outdir+os.sep+"rcrt.dat","w+")
    rcrt_file.write("2\n")
    for i in range(len(polys)):
        inv_area = ((total_outlet_area)/(polys[i].point_data['CenterlineSectionArea'][-1]))
        rcrt_file.write("2\n")
        rcrt_file.write("cap_{}\n".format(i+1))
        rcrt_file.write("{}\n".format(total_resistance*inv_area*resistance_split[0]))
        rcrt_file.write("0.00002\n")
        rcrt_file.write("{}\n".format(total_resistance*inv_area*resistance_split[1]))
        rcrt_file.write("0.0 0.0\n")
        rcrt_file.write("1.0 0.0\n")
    rcrt_file.close()

    # Generate Inflow File
    if steady:
        flow = [tree.data[0,22], tree.data[0,22]]
        time = [0, 1]
        with open(outdir+os.sep+"inflow_1d.flow","w+") as file:
            for i in range(len(time)):
                file.write("{}  {}\n".format(time[i],flow[i]))
        file.close()
    # else:
    #     time,flow = wave(self.data[0,22],self.data[0,21]*2) # changed wave function
    #     time = time.tolist()
    #     flow = flow.tolist()
    #     flow[-1] = flow[0]
    #     period = time[-1]
    #     with open(outdir+os.sep+"inflow_1d.flow","w") as file:
    #         for i in range(len(time)):
    #             file.write("{}  {}\n".format(time[i],flow[i]))
    #     file.close()

    return centerlines_all,polys