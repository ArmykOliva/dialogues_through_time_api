#function to procedurally generate the test of entity
def generate_test(response):
    questions = response.split("\n")
    generated_states = {}
    for i,question in enumerate(questions,1):
        #ask the questions
        generated_states[f"question_{i}"] = {
            "prompt":f"The {i}. questions you need to ask the user is: {question}. Ask him that question.",
            "save_prompt":True,
            "save_ai_msg":True,
            "print_response":True,
            "points_max":len(questions),
            "choices": { 
                "":f"evalueate_answer_{i}"
            },
            "needs_user_input":False
        }
        #evalueate the answer: yes or no
        generated_states[f"evalueate_answer_{i}"] = {
            "prompt":"The user answered with: {{user_msg}}\nDid the user answer the question according to the chat history correctly? (yes/no) Write only 'yes' if he answered correctly and 'no' if he answered incorrectly.",
            "save_prompt":True,
            "save_ai_msg":True,
            "print_response":True,
            "choices": { 
                "yes":f"correct_answer_{i}",
                "no":f"incorrect_answer_{i}"
            },
            "needs_user_input":True
        }
        
        #if answer is yes (correct)
        generated_states[f"correct_answer_{i}"] = {
            "prompt":"The user answered with: {{user_msg}}\nWhich is a correct answer. User gets a point. Respond in one sentence.",
            "save_prompt":True,
            "save_ai_msg":True,
            "print_response":True,
            "choices": { 
                "":f"question_{i+1}" if i <= len(questions)-1 else "end_test"
            },
            "points": 1,
            "needs_user_input":False
        }

        #if answer is no (incorrect)
        generated_states[f"incorrect_answer_{i}"] = {
            "prompt":"The user answered with: {{user_msg}}\nWhich is an incorrect answer. User loses a point. Respond in one sentence.",
            "save_prompt":True,
            "save_ai_msg":True,
            "print_response":True,
            "choices": { 
                "":f"question_{i+1}" if i <= len(questions)-1 else "end_test"
            },
            "points": 0,
            "needs_user_input":False
        }
    
    return generated_states
    