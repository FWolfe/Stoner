#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 15:29:24 2020

@author: wolf
"""
import re
from disco.bot import Plugin
from .. import Program

RE_FILTER = re.compile(r"[^A-Za-z0-9,\./ \~\!\@\#\$\%\^\&\*\(\)\_\-\+\=\|\[\]\{\}\:]")


class ChatterPlugin(Plugin):
    parent = None
    def agent(self):
        return self.parent.agent

    def uncle(self, unique_id):
        return self.bot.client.agent.programs.get(unique_id)


    def train_chatter(self, event):
        chatter = self.uncle('chatter')
        if not chatter:
            return

        for block in re.findall('```(.+?)```', event.content, re.S):
            lines = block.splitlines()
            questions, answers = [], []
            for line in lines:
                if line.startswith('Q:'):
                    questions.append(line[2:].strip())

                elif line.startswith('A:'):
                    answers.append(line[2:].strip())

            chatter.train_question(questions, answers)

        event.reply("Ok.")


    def get_chatter(self, event):
        chatter = self.uncle('chatter')
        if not chatter:
            return None

        text = re.sub(r'(@!?([0-9]+))', '', event.content)
        text = re.sub(r'(?:https?|ftps?)\:\/\/[^\s]*', '', text)
        text = [RE_FILTER.sub('', t) for t in text.splitlines()]
        min_confidence = chatter.config['min_response_confidence']
        default = []
        if event.is_mentioned(self.bot.parent.me.id) or event.guild is None:
            min_confidence = chatter.config['min_response_confidence_mentioned']
            default = ("Sorry you lost me.", "no comment.")

        for line in text:
            chatter.spawn_response(
                text=line,
                min_confidence=min_confidence,
                default=default,
                callback=self.chatter_reply,
                event=event
                )

        return True


    def chatter_reply(self, reply, event, **kwargs):
        if not reply:
            return

        event.reply(reply.text)


    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):

        if not Program.check_access(self, event, require_whitelists=True):
            return

        access = self.bot.get_level(event.author)
        if event.content[0] == self.bot.config.commands_prefix:
            if access == 1000 and event.content[1:6] == 'learn':
                self.train_chatter(event)

            return

        if "```" in event.content:
            return


        self.get_chatter(event)
