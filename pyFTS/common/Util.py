"""
Common facilities for pyFTS
"""

import time
import matplotlib.pyplot as plt
import dill
import numpy as np


def plot_rules(model, size=[5, 5], axis=None, rules_by_axis=None, columns=1):
    if axis is None and rules_by_axis is None:
        rows = 1
    elif axis is None and rules_by_axis is not None:
        rows = (((len(model.flrgs.keys())//rules_by_axis)) // columns)+1

    fig, axis = plt.subplots(nrows=rows, ncols=columns, figsize=size)

    if rules_by_axis is None:
        draw_sets_on_axis(axis, model, size)

    _lhs = model.partitioner.ordered_sets if not model.is_high_order else model.flrgs.keys()

    for ct, key in enumerate(_lhs):

        xticks = []
        xtickslabels = []

        if rules_by_axis is None:
            ax = axis
        else:
            colcount = (ct // rules_by_axis) % columns
            rowcount = (ct // rules_by_axis) // columns

            if rows > 1 and columns > 1:
                ax = axis[rowcount, colcount]
            elif columns > 1:
                ax = axis[rowcount]
            else:
                ax = axis

            if ct % rules_by_axis == 0:
                draw_sets_on_axis(ax, model, size)

        if not model.is_high_order:
            if key in model.flrgs:
                x = (ct % rules_by_axis) + 1
                flrg = model.flrgs[key]
                y = model.sets[key].centroid
                ax.plot([x],[y],'o')
                xticks.append(x)
                xtickslabels.append(key)
                for rhs in flrg.RHS:
                    dest = model.sets[rhs].centroid
                    ax.arrow(x+.1, y, 0.8, dest - y, #length_includes_head=True,
                               head_width=0.1, head_length=0.1, shape='full', overhang=0,
                               fc='k', ec='k')
        else:
            flrg = model.flrgs[key]
            x = (ct%rules_by_axis)*model.order + 1
            for ct2, lhs in enumerate(flrg.LHS):
                y = model.sets[lhs].centroid
                ax.plot([x+ct2], [y], 'o')
                xticks.append(x+ct2)
                xtickslabels.append(lhs)
            for ct2 in range(1, model.order):
                fs1 = flrg.LHS[ct2-1]
                fs2 = flrg.LHS[ct2]
                y = model.sets[fs1].centroid
                dest = model.sets[fs2].centroid
                ax.plot([x+ct2-1,x+ct2], [y,dest],'-')

            y = model.sets[flrg.LHS[-1]].centroid
            for rhs in flrg.RHS:
                dest = model.sets[rhs].centroid
                ax.arrow(x + model.order -1 + .1, y, 0.8, dest - y,  # length_includes_head=True,
                           head_width=0.1, head_length=0.1, shape='full', overhang=0,
                           fc='k', ec='k')


        ax.set_xticks(xticks)
        ax.set_xticklabels(xtickslabels)
        ax.set_xlim([0,rules_by_axis*model.order+1])

    plt.tight_layout()
    plt.show()


def draw_sets_on_axis(axis, model, size):
    if axis is None:
        fig, axis = plt.subplots(nrows=1, ncols=1, figsize=size)
    for ct, key in enumerate(model.partitioner.ordered_sets):
        fs = model.sets[key]
        axis.plot([0, 1, 0], fs.parameters, label=fs.name)
        axis.axhline(fs.centroid, c="lightgray", alpha=0.5)
    axis.set_xlim([0, len(model.partitioner.ordered_sets)])
    axis.set_xticks(range(0, len(model.partitioner.ordered_sets)))
    tmp = ['']
    tmp.extend(model.partitioner.ordered_sets)
    axis.set_xticklabels(tmp)
    axis.set_ylim([model.partitioner.min, model.partitioner.max])
    axis.set_yticks([model.sets[k].centroid for k in model.partitioner.ordered_sets])
    axis.set_yticklabels([str(round(model.sets[k].centroid, 1)) + " - " + k
                          for k in model.partitioner.ordered_sets])


current_milli_time = lambda: int(round(time.time() * 1000))


def uniquefilename(name):
    if '.' in name:
        tmp = name.split('.')
        return  tmp[0] + str(current_milli_time()) + '.' + tmp[1]
    else:
        return name + str(current_milli_time())



def show_and_save_image(fig, file, flag, lgd=None):
    """
    Show and image and save on file

    :param fig: Matplotlib Figure object
    :param file: filename to save the picture
    :param flag: if True the image will be saved
    :param lgd: legend
    """
    if flag:
        plt.show()
        if lgd is not None:
            fig.savefig(file, additional_artists=lgd,bbox_inches='tight')  #bbox_extra_artists=(lgd,), )
        else:
            fig.savefig(file)
        plt.close(fig)


def enumerate2(xs, start=0, step=1):
    for x in xs:
        yield (start, x)
        start += step


def sliding_window(data, windowsize, train=0.8, inc=0.1, **kwargs):
    """
    Sliding window method of cross validation for time series

    :param data: the entire dataset
    :param windowsize: window size
    :param train: percentual of the window size will be used for training the models
    :param inc: percentual of data used for slide the window
    :return: window count, training set, test set
    """
    l = len(data)
    ttrain = int(round(windowsize * train, 0))
    ic = int(round(windowsize * inc, 0))

    progressbar = kwargs.get('progress', None)

    rng = np.arange(0,l-windowsize+ic,ic)

    if progressbar:
        from tqdm import tqdm
        rng = tqdm(rng)

    for count in rng:
        if count + windowsize > l:
            _end = l
        else:
            _end = count + windowsize
        yield (count,  data[count : count + ttrain], data[count + ttrain : _end]  )


def persist_obj(obj, file):
    """
    Persist an object on filesystem. This function depends on Dill package

    :param obj: object on memory
    :param file: file name to store the object
    """
    with open(file, 'wb') as _file:
        dill.dump(obj, _file)


def load_obj(file):
    """
    Load to memory an object stored filesystem. This function depends on Dill package

    :param file: file name where the object is stored
    :return: object
    """
    with open(file, 'rb') as _file:
        obj = dill.load(_file)
    return obj


def persist_env(file):
    """
    Persist an entire environment on file. This function depends on Dill package

    :param file: file name to store the environment
    """
    dill.dump_session(file)


def load_env(file):
    dill.load_session(file)



def start_dispy_cluster(method, nodes):
    import dispy, dispy.httpd, logging

    cluster = dispy.JobCluster(method, nodes=nodes, loglevel=logging.DEBUG, ping_interval=1000)

    http_server = dispy.httpd.DispyHTTPServer(cluster)

    return cluster, http_server



def stop_dispy_cluster(cluster, http_server):
    cluster.wait()  # wait for all jobs to finish

    cluster.print_status()

    http_server.shutdown()  # this waits until browser gets all updates
    cluster.close()



def simple_model_train(model, data, parameters):
    model.train(data, **parameters)
    return model


def distributed_train(model, train_method, nodes, fts_method, data, num_batches=10,
                      train_parameters={}, **kwargs):
    import dispy, dispy.httpd, datetime

    batch_save = kwargs.get('batch_save', False)  # save model between batches

    batch_save_interval = kwargs.get('batch_save_interval', 1)

    file_path = kwargs.get('file_path', None)

    cluster, http_server = start_dispy_cluster(train_method, nodes)

    print("[{0: %H:%M:%S}] Distrituted Train Started".format(datetime.datetime.now()))

    jobs = []
    n = len(data)
    batch_size = int(n / num_batches)
    bcount = 1
    for ct in range(model.order, n, batch_size):
        if model.is_multivariate:
            ndata = data.iloc[ct - model.order:ct + batch_size]
        else:
            ndata = data[ct - model.order: ct + batch_size]

        tmp_model = fts_method(str(bcount))

        tmp_model.clone_parameters(model)

        job = cluster.submit(tmp_model, ndata, train_parameters)
        job.id = bcount  # associate an ID to identify jobs (if needed later)
        jobs.append(job)

        bcount += 1

    for job in jobs:
        print("[{0: %H:%M:%S}] Processing batch ".format(datetime.datetime.now()) + str(job.id))
        tmp = job()
        if job.status == dispy.DispyJob.Finished and tmp is not None:
            model.merge(tmp)

            if batch_save and (job.id % batch_save_interval) == 0:
                persist_obj(model, file_path)

        else:
            print(job.exception)
            print(job.stdout)

        print("[{0: %H:%M:%S}] Finished batch ".format(datetime.datetime.now()) + str(job.id))

    print("[{0: %H:%M:%S}] Distrituted Train Finished".format(datetime.datetime.now()))

    stop_dispy_cluster(cluster, http_server)

    return model



def simple_model_predict(model, data, parameters):
    return model.predict(data, **parameters)



def distributed_predict(model, parameters, nodes, data, num_batches):
    import dispy, dispy.httpd

    cluster, http_server = start_dispy_cluster(simple_model_predict, nodes)

    jobs = []
    n = len(data)
    batch_size = int(n / num_batches)
    bcount = 1
    for ct in range(model.order, n, batch_size):
        if model.is_multivariate:
            ndata = data.iloc[ct - model.order:ct + batch_size]
        else:
            ndata = data[ct - model.order: ct + batch_size]

        job = cluster.submit(model, ndata, parameters)
        job.id = bcount  # associate an ID to identify jobs (if needed later)
        jobs.append(job)

        bcount += 1

    ret = []

    for job in jobs:
        tmp = job()
        if job.status == dispy.DispyJob.Finished and tmp is not None:
            if job.id < batch_size:
                ret.extend(tmp[:-1])
            else:
                ret.extend(tmp)
        else:
            print(job.exception)
            print(job.stdout)

    stop_dispy_cluster(cluster, http_server)

    return ret
