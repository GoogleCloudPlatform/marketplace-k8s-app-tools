import yaml 

docstart = "---\n"

def load_resources_yaml(filename):
  ''' Loads kubernetes resource from .yaml '''

  docs_yaml = []
  print("Reading " + filename)
  with open(filename, "r") as stream:
    content = stream.read()
    docs = content.split(docstart)
    for doc in docs:
      if len(doc) > 0:
        doc_yaml = yaml.load(doc)
        if doc_yaml and 'kind' in doc_yaml:
          print("  {:s}/{:s}".format(doc_yaml['kind'], doc_yaml['metadata']['name']))
          docs_yaml.append(doc_yaml)
  
  return docs_yaml