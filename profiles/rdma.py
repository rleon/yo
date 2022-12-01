from collections import OrderedDict
from utils.misc import fix_gpg_key

class LRProfile():
    def __init__(self):

        self.upload = {}
        # Branches without -f push
        self.upload["no_force"] = {
                # remote : [(local branch, remote branch)]
                "origin" : [("master", "master")],
                "ver" : [("master", "master")],
                "ml" : [("master", "master") ,
                         ("mlx5-next", "mlx5-next")
                ],
                "rdma" : [("wip/leon-for-next", "wip/leon-for-next"),
                          ("wip/leon-for-rc", "wip/leon-for-rc")
                ]
        }

        # Branches with -f push
        self.upload["force"] = {
                # remote : [(local branch, remote branch)]
                "origin" : [("rdma-next", "rdma-next"),
                            ("rdma-rc", "rdma-rc")],
                "ver" : [("testing/rdma-next", "testing/rdma-next"),
                         ("testing/rdma-rc", "testing/rdma-rc"),
                         ("queue-next", "queue-next"),
                         ("queue-rc", "queue-rc")
                ]
        }

        # Cross check to see if local branch has updated remote branch
        self.upload["cross_check"] = {
                # remote : [(local branch, remote branch)]
                "ver" : [("queue-next", "testing/net-next"),
                         ("queue-next", "testing/net-rc"),
                         ("queue-rc", "testing/net-rc")

                ]
        }

        self.update = {}
        self.update["remotes"] = ["ver",
                                  "linus",
                                  "origin",
                                  "rdma",
                                  "ipsec",
                                  "ipsec-next",
                                  "ml",
                                  "net",
                                  "net-next",
                                  "vfio"
        ]

        self.update["tags"] = {
                # remote : [(local branch, remote branch)]
                "linus" : [("master", "master")]
        }

        self.update["rebases"] = OrderedDict()
        self.update["rebases"] = {
                "rdma-rc" : "wip/leon-for-rc",
                "rdma-next" : "wip/leon-for-next",
                "xfrm-next" : "ipsec-next/master",
                "vfio-next" : "vfio/next",
                "net-next" : "net-next/master",
                "net" : "net/master"
        }

        self.update["merges"] = OrderedDict()
        self.update["merges"] = {
                # local branch : [base, source branches]
                "mlx5-next" : ["ml/mlx5-next"],
                "testing/rdma-rc" : ["rdma-rc", "master", "vfio/for-linus", "ipsec/master"],
                "testing/rdma-next" : ["testing/rdma-rc", "rdma-next", "rdma/hmm",
                                                           "vfio-next", "xfrm-next"],
                "queue-rc" : ["ver/testing/net-rc", "testing/rdma-rc"],
                "queue-next" : ["ver/testing/net-next", "testing/rdma-next"]
        }

        self.setup = {}
        self.setup["remotes"] = {
                # remote : [fetch, push]
                "ipsec" : ["https://git.kernel.org/pub/scm/linux/kernel/git/klassert/ipsec.git"],
                "ipsec-next" : ["https://git.kernel.org/pub/scm/linux/kernel/git/klassert/ipsec-next.git"],
                "jgg" : ["https://github.com/jgunthorpe/linux.git"],
                "linus"	: ["https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"],
                "mellanox" : ["ssh://leonro@l-gerrit.mtl.labs.mlnx:29418/upstream/linux"],
                "ml" : ["https://git.kernel.org/pub/scm/linux/kernel/git/mellanox/linux.git",
                        "gt@gitolite.kernel.org:pub/scm/linux/kernel/git/mellanox/linux"],
                "net" : ["https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net.git"],
                "net-next" : ["https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git"],
                "origin" : ["https://git.kernel.org/pub/scm/linux/kernel/git/leon/linux-rdma.git",
                            "git@gitolite.kernel.org:pub/scm/linux/kernel/git/leon/linux-rdma"],
                "rdma" : ["https://git.kernel.org/pub/scm/linux/kernel/git/rdma/rdma.git",
                          "git@gitolite.kernel.org:pub/scm/linux/kernel/git/rdma/rdma"],
                "saeed" : ["https://git.kernel.org/pub/scm/linux/kernel/git/saeed/linux.git"],
                "ver" : ["git@github.com:Mellanox/nic-kernel.git"],
                "vfio" : ["https://github.com/awilliam/linux-vfio.git"]
        }

        self.setup["branches"] = {
                # branch : base
                "master" : "origin/master",
                "rdma-next" : "origin/rdma-next",
                "queue-next" : "ver/queue-next",
                "queue-rc" : "ver/queue-rc",
                "testing/rdma-next" : "ver/testing/rdma-next",
                "testing/rdma-rc" : "ver/testing/rdma-rc",
                "rdma-rc" : "origin/rdma-rc",
                "vfio-next" : "vfio/next",
                "xfrm-next" : "ipsec-next/master",
                "net-next" : "net-next/master",
                "net" : "net/master",
                "mlx5-next" : "ml/mlx5-next",
                "wip/leon-for-next" : "rdma/wip/leon-for-next",
                "wip/leon-for-rc" : "rdma/wip/leon-for-rc"
        }

        self.verify = {}
        self.verify["branches"] = {
                # branch to test : changeID
                "rdma-next" : "Iaaf0a270fff9fb7537bee5b90d53a5dff51238a8",
                "testing/rdma-next" : "Iaaf0a270fff9fb7537bee5b90d53a5dff51238a9",
                "rdma-rc" : "I57c11684febd2aa97ebb44ae82368466458dd8f4",
                "testing/rdma-rc" : "Iaaf0a270fff9fb7537bee5b90d53a5dff51238b9",
                "queue-next" : "I57c11684febd2aa97ebb44ae82368466458dd8f5",
                "queue-rc" : "I57c11684febd2aa97ebb44ae82368466458dd8f6",
                "xfrm-next" : "I57c11684febd2aa97ebb54ae82368477458dd8f8",
                "vfio-next" : "I57c11684febd3aa97ebb54ae82368477458dd8f8",
        }
        self.verify["current"] = "I57c11684febd3aa97ebb54ae82368477458dd8f6"
        self.verify["bases"] = ["rdma-next-mlx", "net-next",
                                "rdma-rc-mlx", "net"]

    def setup_connection(self):
        fix_gpg_key();
