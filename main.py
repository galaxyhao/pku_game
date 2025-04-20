#!/usr/bin/env python3
# coding: utf-8

from gamer import PKUGamer, AnswerType, QuestionType


# —— 地点列表 —— #
PLACES = ["未名湖", "百年讲堂", "图书馆", "西门", "燕南园"]
QTYPE = ["选择题", "简答题"]

def main():
    gamer = PKUGamer()
    print("🎓 欢迎来到北大知识问答游戏！（输入 q 退出）")

    while True:
        place = input(f"\n🏞️ 请选择地点（{', '.join(PLACES)}）或输入 q 退出: ")
        if place.lower() == 'q':
            break
        if place not in PLACES:
            print("❗ 无效地点，请重新输入")
            continue

        question_type = input(f"\n🏞️ 请选择题目类型（{', '.join(QTYPE)}）或输入 q 退出: ")
        if question_type.lower() == 'q':
            break
        if question_type not in QTYPE:
            print("❗ 无效题目类型，请重新输入")
            continue

        # 生成题目
        print("🤖 生成题目中...")
        q_type = QuestionType.QUESTION
        if question_type == "选择题":
            q_type = QuestionType.OPT_QUESTION

        qa_text, answer_text = gamer.ask_question(place, q_type)
        print("\n🎯 题目已生成：")
        print(qa_text)

        while True:
            # 用户作答
            user_answer = input("\n📝 你的回答是：\n")

            result = gamer.answer(user_answer)
            if result.answer_type == AnswerType.HINT:
                print("\n💡 提示：")
                print(result.hint)
            else:
                print(f"\n📢 评分结果：{result.score}, 理由: {result.comment}")
                print(f"正确答案：{answer_text}")
                break

        gamer.reset()

if __name__ == "__main__":
    main()
