from llm.trainer import LLMIns

if __name__ == "__main__":
    model = LLMIns()
    model.create_semantic_txt()
    query = "What has been happening with cyber insurance pricing?"

    response = model.falcon_with_articles(query)

    print(response)

# query = "Have kingstone finalised their reinsurance? and how much did they renew it for?"
