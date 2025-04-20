import logging
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from prompt_tpl import tql_question, tql_score, tql_hint, tql_route, tql_opt_question
from enum import Enum
import json
from dataclasses import dataclass

class QuestionType(Enum):
    QUESTION = "question"
    OPT_QUESTION = "opt_question"

class AnswerType(Enum):
    ANSWER = "answer"
    HINT = "hint"

class GamerState(Enum):
    INIT = "init"
    QUESTION_GENERATED = "question_generated"
    ANSWER_EVALUATED = "answer_evaluated"


@dataclass
class AnswerResult:
    answer_type: AnswerType
    score: int = 0
    comment: str = ""
    hint: str = ""
    answer_T: str = ""

class PKUGamer:
    def __init__(self):
        self.__state: GamerState = GamerState.INIT
        self.__question = ""
        self.__answer_T = ""
        self.__score = 0
        self.__q_type = None
        # self.memory = ConversationBufferMemory()

        llm = ChatOpenAI(
            openai_api_key=os.getenv("ARK_API_KEY"),
            openai_api_base=os.getenv("ARK_API_BASE"),
            model_name="doubao-1-5-pro-32k-250115",
            temperature=0.7,
        )

        question = PromptTemplate(template=tql_question, input_variables=["place"])
        self.__chain_q = question | llm

        opt_question = PromptTemplate(template=tql_opt_question, input_variables=["place"])
        self.__chain_opt_q = opt_question | llm

        score = PromptTemplate(template=tql_score, input_variables=["question", "answer"])
        self.__chain_s = score | llm

        hint = PromptTemplate(template=tql_hint, input_variables=["answer"])
        self.__chain_h = hint | llm

        router = PromptTemplate(template=tql_route, input_variables=["user_input", "question"])
        self.__chain_r = router | llm

    def ask_question(self, place: str, q_type: QuestionType) -> (str, str):
        if self.__state != GamerState.INIT:
            raise RuntimeError("invalid state, must be INIT")

        if q_type == QuestionType.QUESTION:
            resp = self.__chain_q.invoke({
                "place": place,
            })
            result = json.loads(resp.content)
            self.__question = result["question"]
            self.__answer_T = result["answer"]
        else:
            resp = self.__chain_opt_q.invoke({
                "place": place,
            })
            result = json.loads(resp.content)
            self.__question = result["question"]
            for key in sorted(result["options"]):
                self.__question += f"\n{key}. {result['options'][key]}"

            self.__answer_T = result["answer"]

        self.__state = GamerState.QUESTION_GENERATED
        self.__q_type = q_type
        return self.__question, self.__answer_T

    def answer(self, answer) -> AnswerResult:
        if self.__state != GamerState.QUESTION_GENERATED:
            raise RuntimeError("invalid state, must be QUESTION_GENERATED")

        rou_resp = self.__chain_r.invoke({
            "question": self.__question,
            "user_input": answer,
        })

        if AnswerType.HINT.value in rou_resp.content:
            hint_text = self.__get_hint()
            return AnswerResult(AnswerType.HINT, hint=hint_text)
        elif self.__q_type == QuestionType.QUESTION:
            score, comment = self.__evaluate_answer(answer)
            return AnswerResult(AnswerType.ANSWER, score=score, comment=comment, answer_T=self.__answer_T)
        else:
            if answer in self.__answer_T:
                return AnswerResult(AnswerType.ANSWER, score=10, answer_T=self.__answer_T)
            else:
                return AnswerResult(AnswerType.ANSWER, score=0, answer_T=self.__answer_T)

    def reset(self):
        self.__state = GamerState.INIT
        self.__question = None
        self.__question = ""
        self.__answer_T = ""
        self.__score = 0

    def __evaluate_answer(self, answer) -> (int, str):
        if self.__state!= GamerState.QUESTION_GENERATED:
            raise RuntimeError("invalid state, must be QUESTION_GENERATED")
        resp = self.__chain_s.invoke({
            "question": self.__question,
            "answer": answer,
        })

        logging.info(resp.content)
        result = json.loads(resp.content)
        self.__score = result["score"]
        self.__state = GamerState.ANSWER_EVALUATED

        return self.__score, result["comment"]


    def __get_hint(self) -> str:
        if self.__state!= GamerState.QUESTION_GENERATED:
            raise RuntimeError("invalid state, must be QUESTION_GENERATED")

        resp = self.__chain_h.invoke({
            "question": self.__question,
        })

        return resp.content