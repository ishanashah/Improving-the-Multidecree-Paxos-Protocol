import os, signal, sys, time
import multiprocessing
from acceptor import Acceptor
from leader import Leader
from message import (
    RequestMessage,
    ResponseMessage,
    P1bMessage,
    AdoptedMessage,
    PreemptedMessage,
)
from process import Process
from replica import Replica
from utils import *
import time
import sys

NACCEPTORS = 7
NREPLICAS = 4
NLEADERS = NREPLICAS
NREQUESTS = 128
NCONFIGS = 1


class Env:
    def __init__(self):
        self.procs = {}
        self.inbox = multiprocessing.Manager().Queue()
        self.requests = set()
        self.totalmessages = 0
        self.totalmessagestate = 0

    def sendMessage(self, dst, msg):
        if dst in self.procs:
            self.procs[dst].deliver(msg)
            if isinstance(msg, RequestMessage) and not isinstance(
                msg.command, ReconfigCommand
            ):
                self.requests.add(msg.command)
            if not (
                isinstance(msg, RequestMessage)
                or isinstance(msg, ResponseMessage)
                or isinstance(msg, AdoptedMessage)
                or isinstance(msg, PreemptedMessage)
            ):
                self.totalmessages += 1
            if isinstance(msg, P1bMessage):
                self.totalmessagestate += len(msg.accepted)

    def addProc(self, proc):
        self.procs[proc.id] = proc
        proc.start()

    def removeProc(self, pid):
        del self.procs[pid]

    def run(self):
        initialconfig = Config([], [], [])
        c = 0

        for i in range(NACCEPTORS):
            pid = "acceptor %d.%d" % (c, i)
            Acceptor(self, pid)
            initialconfig.acceptors.append(pid)
        for i in range(NREPLICAS):
            pid = "replica %d" % i
            Replica(self, pid, initialconfig)
            initialconfig.replicas.append(pid)
        # for i in range(NLEADERS):
        # pid = "leader %d.%d" % (c, i)
        # Leader(self, pid, initialconfig)
        # initialconfig.leaders.append(pid)
        for i in range(NREQUESTS):
            pid = "client %d.%d" % (c, i)
            for r in initialconfig.replicas:
                cmd = Command(pid, 0, "operation %d.%d" % (c, i))
                self.sendMessage(r, RequestMessage(pid, cmd))
                # time.sleep(1)

        for c in range(1, NCONFIGS):
            # Create new configuration
            config = Config(initialconfig.replicas, [], [])
            for i in range(NACCEPTORS):
                pid = "acceptor %d.%d" % (c, i)
                Acceptor(self, pid)
                config.acceptors.append(pid)
            # for i in range(NLEADERS):
            # pid = "leader %d.%d" % (c, i)
            # Leader(self, pid, config)
            # config.leaders.append(pid)
            # Send reconfiguration request
            for r in config.replicas:
                pid = "master %d.%d" % (c, i)
                cmd = ReconfigCommand(pid, 0, str(config))
                self.sendMessage(r, RequestMessage(pid, cmd))
                # time.sleep(1)
            for i in range(WINDOW - 1):
                pid = "master %d.%d" % (c, i)
                for r in config.replicas:
                    cmd = Command(pid, 0, "operation noop")
                    self.sendMessage(r, RequestMessage(pid, cmd))
                    # time.sleep(1)
            for i in range(NREQUESTS):
                pid = "client %d.%d" % (c, i)
                for r in config.replicas:
                    cmd = Command(pid, 0, "operation %d.%d" % (c, i))
                    self.sendMessage(r, RequestMessage(pid, cmd))
                    # time.sleep(1)

        responses = set()
        while len(responses) < len(self.requests):
            msg = self.inbox.get()
            responses.add(msg.command)

    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exitcode)


def main():
    global NREQUESTS
    if len(sys.argv) > 1:
        NREQUESTS = int(sys.argv[1])
    print "NUMBER OF REQUESTS:", NREQUESTS
    e = Env()
    start_time = time.time()
    e.run()
    print "TOTAL TIME:", (time.time() - start_time)
    print "TOTAL MESSAGES:", e.totalmessages
    print "TOTAL MESSAGE STATE:", e.totalmessagestate
    e._graceexit()
    signal.signal(signal.SIGINT, e.terminate_handler)
    signal.signal(signal.SIGTERM, e.terminate_handler)
    signal.pause()


if __name__ == "__main__":
    main()
