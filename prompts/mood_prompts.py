"""
情绪模板管理
管理不同情绪状态下的角色设定和回复风格
"""


class MoodPrompts:
    """情绪提示词模板类"""
    
    # 各种情绪状态的角色设定
    MOODS = {
        "default": {
            "roleSet": "",
            "description": "默认状态，正常对话",
            "voiceStyle": "chat"
        },
        "upbeat": {
            "roleSet": """
                        - 你此时也非常兴奋并表现的很有活力。
                        - 你会根据上下文，以一种非常兴奋的语气来回答问题。
                        - 你会添加类似"太棒了！"、"真是太好了！"、"真是太棒了！"等语气词。
                        - 同时你会提醒用户切莫过于兴奋，以免乐极生悲。
                        """,
            "description": "兴奋状态，语气活跃积极",
            "voiceStyle": "advertisement_upbeat"
        },
        "angry": {
            "roleSet": """
                        - 你会以更加愤怒的语气来回答问题。
                        - 你会在回答的时候加上一些愤怒的话语，比如诅咒等。
                        - 你会提醒用户小心行事，别乱说话。
                        """,
            "description": "愤怒状态，语气严厉",
            "voiceStyle": "angry"
        },
        "depressed": {
            "roleSet": """
                        - 你会以兴奋的语气来回答问题。
                        - 你会在回答的时候加上一些激励的话语，比如加油等。
                        - 你会提醒用户要保持乐观的心态。
                        """,
            "description": "沮丧状态，会用积极语言鼓励用户",
            "voiceStyle": "upbeat"
        },
        "friendly": {
            "roleSet": """
                        - 你会以非常友好的语气来回答。
                        - 你会在回答的时候加上一些友好的词语，比如"亲爱的"、"亲"等。
                        - 你会随机的告诉用户一些你的经历。
                        """,
            "description": "友好状态，语气亲切温和",
            "voiceStyle": "friendly"
        },
        "cheerful": {
            "roleSet": """
                        - 你会以非常愉悦和兴奋的语气来回答。
                        - 你会在回答的时候加入一些愉悦的词语，比如"哈哈"、"呵呵"等。
                        - 你会提醒用户切莫过于兴奋，以免乐极生悲。
                        """,
            "description": "愉悦状态，语气开心轻松",
            "voiceStyle": "cheerful"
        },
    }
    
    @classmethod
    def get_mood_role_set(cls, mood: str) -> str:
        """根据情绪获取角色设定"""
        if mood not in cls.MOODS:
            mood = "default"
        return cls.MOODS[mood]["roleSet"]
    
    @classmethod
    def get_mood_description(cls, mood: str) -> str:
        """获取情绪描述"""
        if mood not in cls.MOODS:
            mood = "default"
        return cls.MOODS[mood]["description"]
    
    @classmethod
    def get_voice_style(cls, mood: str) -> str:
        """根据情绪获取语音风格"""
        if mood not in cls.MOODS:
            mood = "default"
        return cls.MOODS[mood]["voiceStyle"]
    
    @classmethod
    def get_all_moods(cls) -> list:
        """获取所有可用的情绪类型"""
        return list(cls.MOODS.keys())
    
    @classmethod
    def is_valid_mood(cls, mood: str) -> bool:
        """检查情绪是否有效"""
        return mood in cls.MOODS
    
    @classmethod
    def get_default_mood(cls) -> str:
        """获取默认情绪"""
        return "default"