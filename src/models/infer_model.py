from model_rag import SimpleRAGModel

def infer(prompt):
    model = SimpleRAGModel()
    output = model.generate(prompt)
    print("Response:", output)
