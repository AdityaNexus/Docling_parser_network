from docling.document_converter import DocumentConverter    

converter = DocumentConverter()
#result = converter.convert("https://arxiv.org/pdf/2408.09869")

# document = result.document
# markdown_output = document.export_to_markdown()
# json_output = document.export_to_dict()

#with open("markdown.md","w",encoding = "utf-8") as file:
  # file.write(markdown_output)

result = converter.convert("https://docs.langchain.com/oss/python/langchain/mcp")

document = result.document
markdown_output = document.export_to_markdown()
print(markdown_output)

