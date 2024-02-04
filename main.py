from argparse import ArgumentParser
from spade import wait_until_finished, run
from agentMailSender import AgentMailSender
from agentSearcher import AgentSearcher

async def main():
    agent_mail_sender = AgentMailSender(args.jid2, args.pwd2)
    agent_searcher = AgentSearcher(args.jid1, args.pwd1, args.checkPricesMinutes)
    
    await agent_mail_sender.start()
    await agent_searcher.start()

    await wait_until_finished(agent_mail_sender)
    await wait_until_finished(agent_searcher)
    


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-jid1", type=str, help="JID 1. agenta (Agent searcher)", default="agent1@DESKTOP-TQI23PE")
    parser.add_argument("-pwd1", type=str, help="Lozinka 1. agenta (Agent searcher)", default="123")
    parser.add_argument("-jid2", type=str, help="JID 2. agenta (Agent mail sender)", default="agent2@DESKTOP-TQI23PE")
    parser.add_argument("-pwd2", type=str, help="Lozinka 2. agenta (Agent mail sender)", default="123")
    parser.add_argument("-checkPricesMinutes", type=int, help="Refresh i provjera cijena nabava.net svakih n minuta")
    
    args = parser.parse_args()
    
    run(main())