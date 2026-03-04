from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'tharusha@2001'))
with driver.session() as session:
    result = session.run('MATCH (p:Person) RETURN p LIMIT 1')
    person = result.single()['p']
    print('Person properties:', dict(person))
driver.close()
