#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reflexion: self-evaluation and improvement suggestions based on episodes and results
"""
import openai, time
from config import OPENAI_API_KEY, LLM_MODEL
from core.memory import semantic_search, add_episode
openai.api_key = OPENAI_API_KEY

def reflect_on_recent(n=6):
    hits = semantic_search('recent', top_k=n)
    prompt = 'You are a meta-critic. Read these recent episodes and propose 3 improvements or next actions with brief justification.\n\nContext:\n'

    for h in hits:
        prompt += h.get('doc','')[:600] + '\n---\n'

    resp = openai.ChatCompletion.create(model=LLM_MODEL, messages=[{'role':'user','content':prompt}], max_tokens=400, temperature=0.2)
    text = resp.choices[0].message.content
    add_episode('reflexion', text)
    return text
