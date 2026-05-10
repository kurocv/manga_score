#!/usr/bin/python
# -*- coding: utf-8 -*-

from manga_score_service import MangaScoreService

class MangaScoreViewModel:    
    def __init__(self, service: MangaScoreService):
        self.service = service

    def on_closing(self):
        print("vm 終了処理中...")




