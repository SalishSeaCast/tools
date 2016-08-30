import numpy as np


def mean_tracer_at_depth(grid_t, tracer_name, min_depth = 150, max_depth = None):
    t = np.array([float(x) for x in grid_t.time_centered.values])
    days = (t[:] - t[0])/10**9/3600/24
    min_day_index = np.argmax(days > 30)
    max_day_index = len(days)

    grid_heights = grid_t.deptht_bounds.values[:, 1] - grid_t.deptht_bounds.values[:, 0]
    depths = grid_t.deptht.values
    min_depth_index = np.argmax(depths > min_depth)
    if(max_depth and max_depth < max(depths)):
        max_depth_index = np.argmax(depths > max_depth)
    else:
        max_depth_index = len(depths)

    tracer_quantity_array = ((grid_t[tracer_name].values)*(grid_heights.reshape((1, 40, 1, 1))))
    total_tracer_at_depth = tracer_quantity_array[min_day_index:max_day_index, min_depth_index:max_depth_index, :, :].sum()
    mean_tracer = total_tracer_at_depth/sum(grid_heights[min_depth_index:max_depth_index])/(max_day_index - min_day_index)
    mean_tracer = mean_tracer/15  # number of non-zero grid elements in 5x5 model
    return(mean_tracer)


def mean_NH4_at_depth(grid_t):
    return(mean_tracer_at_depth(grid_t, "NH4"))


def mean_NO3_at_depth(grid_t):
    return(mean_tracer_at_depth(grid_t, "NO3"))

def mean_NO3_at_20m(grid_t):
    return(mean_tracer_at_depth(grid_t, "NO3", 15, 25))

def mean_DON_at_depth(grid_t):
    return(mean_tracer_at_depth(grid_t, "DOC"))


def mean_PON_at_depth(grid_t):
    return(mean_tracer_at_depth(grid_t, "POC"))


def time_of_peak_PHY2(grid_t):
    t = np.array([float(x) for x in grid_t.time_centered.values])
    days = (t[:] - t[0])/10**9/3600/24
    grid_heights = grid_t.deptht_bounds.values[:, 1] - grid_t.deptht_bounds.values[:, 0]

    phy2_quantity_array = ((grid_t["PHY2"].values)*(grid_heights.reshape((1, 40, 1, 1))))
    total_phy2 = phy2_quantity_array.sum((1, 2, 3))
    bloom_time = days[int(np.argmax(total_phy2))]
    return(bloom_time)


def time_surface_NO3_drops_below_4(grid_t):
    t = np.array([float(x) for x in grid_t.time_centered.values])
    days = (t[:] - t[0])/10**9/3600/24
    grid_heights = grid_t.deptht_bounds.values[:, 1] - grid_t.deptht_bounds.values[:, 0]

    mean_surface_NO3 = np.sum(((grid_t.variables["NO3"][:, :, 1, 1]*grid_heights.reshape((1, 40)))[:, :10]/sum(grid_heights[:10])), axis = 1)
    bloom_time = days[int(np.argmax(mean_surface_NO3 < 4))]
    return(bloom_time)


def peak_3_day_biomass(grid_t):
    t = np.array([float(x) for x in grid_t.time_centered.values])
    days = (t[:] - t[0])/10**9/3600/24
    grid_heights = grid_t.deptht_bounds.values[:, 1] - grid_t.deptht_bounds.values[:, 0]
    reshaped_grid_heights = grid_heights.reshape((1, 40, 1, 1))
    N = np.argmax(days > 3)  # time steps for 3 days
    
    
    
    primary_producers = ["PHY", "PHY2", "MYRI"]
    depth_integrated = np.zeros(grid_t.dims['time_counter'])
    for tracer in primary_producers:
        depth_integrated = depth_integrated + np.sum((grid_t[tracer].values)*reshaped_grid_heights, axis = (1, 2, 3))

    time_averaged = np.convolve(depth_integrated, np.ones((N,))/N, mode='valid')
    return(time_averaged.max())
