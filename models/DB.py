import psycopg2
import psycopg2.extras
from psycopg2 import sql


class DB:

    # use property for lazy loading later

    def __init__(self, database, user, password, host="localhost", port="5432"):
        self.conn = psycopg2.connect(database=database, user=user,
                                     password=password, host=host, port=port)

        self.cursor = self.conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

    def getInsertQuery(self, table, columns, returning=False):
        query_statement = "INSERT INTO {table} ({cols}) VALUES ({values})"
        suffix = "RETURNING id" if returning else ""
        query_statement += suffix + ";"

        query = sql.SQL(query_statement).format(
            table=sql.Identifier(table),
            cols=sql.SQL(', ').join(map(sql.Identifier, columns)),
            values=sql.SQL(', ').join(sql.Placeholder()*len(columns))
        )
        return query

    def selectHelper(self, table, user, offset=0, limit=50, filters={}):
        user_id = self.getID("users", {"username": user})

        query_statement = """
        SELECT t1.*, count(t1.*) OVER() as full_count FROM
        ({table} LEFT JOIN save_tags_view USING(user_save_id)) as t1
        WHERE t1.user_id={user_id}
        """

        search_text = ""
        subs = {}

        additional = list()

        if filters["search"]:
            filters["search"] = filters["search"].lower()
            if table == "comments":
                search_text = "body_html"
            else:
                search_text = "link_title"

            additional.append("LOWER(t1.{search_text}) LIKE {search}")

        if filters["subreddit"]:
            subs.update({k: k for k in filters["subreddit"]})
            additional.append("LOWER(t1.subreddit) IN ({subreddit})")

        if additional:
            query_statement += " AND " + " AND ".join(additional)

        query_statement += "ORDER BY user_save_id DESC LIMIT {limit} offset {offset}"

        # print(query_statement)
        query = sql.SQL(query_statement).format(
            table=sql.Identifier(table),
            user_id=sql.Placeholder("user_id"),
            offset=sql.Placeholder("offset"),
            limit=sql.Placeholder("limit"),
            search_text=sql.Identifier(search_text),
            search=sql.Placeholder("search"),
            subreddit=sql.SQL(", ").join(map(sql.Placeholder, filters["subreddit"]) if filters["subreddit"] else []))

        query_dict = {"offset": offset, "user_id": user_id,
                      "limit": limit}
        query_dict.update({"search": f'%{filters["search"]}%'})
        query_dict.update(subs)
        print(query.as_string(self.conn))
        self.cursor.execute(
            query, (query_dict))
        result = self.cursor.fetchall()

        return result

    def mergeSorted(self, table1, table2, col, limit):
        result = list()
        l1 = len(table1)
        l2 = len(table2)
        i = j = 0
        while(i < l1 and j < l2):
            if(table1[i][col] > table2[j][col]):
                result.append(table1[i])
                i += 1
            else:
                result.append(table2[j])
                j += 1
        if i != l1:
            result.extend(table1[i:])
        elif j != l2:
            result.extend(table2[j:])

        return result[:limit]

    def selectUserSaves(self, user, offset=0, limit=50, filters={}):
        links_count = 0
        comments_count = 0

        links = self.selectHelper(
            "links_view", user, offset=offset, limit=limit, filters=filters)
        if links:
            links_count = links[0]["full_count"]

        if filters and filters["save_type"] == "post":
            return (links, links_count)

        comments = self.selectHelper(
            "comments_view", user, offset=offset, limit=limit, filters=filters)

        if comments:
            comments_count = comments[0]["full_count"]

        if filters and filters["save_type"] == "comment":
            return (comments, comments_count)

        res = self.mergeSorted(links, comments, "user_save_id", limit)
        return (res, links_count+comments_count)

    def insert(self, table, params, returning=False):
        query = self.getInsertQuery(table, params.keys(), returning)
        print(query.as_string)
        try:
            self.cursor.execute(query, tuple(params.values()))
            returned = self.cursor.fetchone()["id"] if returning else None

        except psycopg2.Error as e:
            print(e)
            self.conn.rollback()
            return

        else:
            # print("Commited to {}".format(table), end="\n\n")
            self.conn.commit()
            return returned

    def encode(self, key):
        query = sql.SQL(' = ').join((sql.Identifier(key), sql.Placeholder()))
        return query

    def recordExists(self, table, params):
        query_statement = "SELECT EXISTS(SELECT 1 FROM {table} WHERE {params})"

        query = sql.SQL(query_statement).format(
            table=sql.Identifier(table),
            params=sql.SQL(' and ').join(
                map(self.encode, params.keys())
            )
        )

        self.cursor.execute(
            query, tuple(params.values()))

        self.conn.commit()
        res = self.cursor.fetchone()

        return res["exists"]

    def getID(self, table, params):
        query_statement = "SELECT id FROM {table} WHERE {params}"

        query = sql.SQL(query_statement).format(
            table=sql.Identifier(table),
            params=sql.SQL(' and ').join(
                map(self.encode, params.keys())
            )
        )

        self.cursor.execute(
            query, tuple(params.values()))

        self.conn.commit()

        res = self.cursor.fetchone()
        return res["id"] if res else None

    def close(self):
        self.conn.close()
        self.cursor.close()
