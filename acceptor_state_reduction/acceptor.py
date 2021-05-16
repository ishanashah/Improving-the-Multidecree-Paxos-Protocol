from utils import PValue
from process import Process
from message import P1aMessage, P1bMessage, P2aMessage, P2bMessage


class Acceptor(Process):
    def __init__(self, env, id):
        Process.__init__(self, env, id)
        self.ballot_number = None
        self.accepted = {}
        self.env.addProc(self)

    def body(self):
        # print "Here I am: ", self.id
        while True:
            msg = self.getNextMessage()
            if isinstance(msg, P1aMessage):
                if msg.ballot_number > self.ballot_number:
                    self.ballot_number = msg.ballot_number
                self.sendMessage(
                    msg.src,
                    P1bMessage(self.id, self.ballot_number, self.accepted.values()),
                )
            elif isinstance(msg, P2aMessage):
                if msg.ballot_number == self.ballot_number:
                    # self.accepted.add(
                    #     PValue(msg.ballot_number, msg.slot_number, msg.command)
                    # )
                    self.accepted[msg.slot_number] = PValue(
                        msg.ballot_number, msg.slot_number, msg.command
                    )
                self.sendMessage(
                    msg.src, P2bMessage(self.id, self.ballot_number, msg.slot_number)
                )
