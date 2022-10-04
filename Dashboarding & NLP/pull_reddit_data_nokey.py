import pandas as pd
import numpy as np
import requests

#%%
#declare tokens for API

client_id = ''
secret_token = ''
username = ''
pw = ''

# note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
auth = requests.auth.HTTPBasicAuth(client_id, secret_token)

# here we pass our login method (password), username, and password
data = {'grant_type': 'password',
        'username': username,
        'password': pw}

# setup our header info, which gives reddit a brief description of our app
headers = {'User-Agent': 'MyBot/0.0.1'}

# send our request for an OAuth token
res = requests.post('https://www.reddit.com/api/v1/access_token',
                    auth=auth, data=data, headers=headers)

# convert response to JSON and pull access_token value
TOKEN = res.json()['access_token']
# TOKEN = res.json()

# add authorization to our headers dictionary
headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

# while the token is valid (~2 hours) we just add headers=headers to our requests
requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)

#%%

#define functions for pulling post info and comment info
comment_metrics = ['id','subreddit_id','subreddit','parent_id','body','total_awards_received','score','created_utc']
post_metrics = ['subreddit','url','score','upvote_ratio','num_comments','gilded','view_count','name','created_utc']

def get_results(r,metrics):
    '''
    Create a DataFrame Showing Title, URL, Score and Number of Comments.
    '''
    myDict = {}
    for post in r['data']['children']:
        myDict[post['data']['title']] = {m:post['data'][m] for m in metrics}
    df = pd.DataFrame.from_dict(myDict, orient='index')
    df.index.name = 'title'
    return df.reset_index()

def extract_comment_data(comments_json,metrics):
    """
    comments_json should be a list of comment objects with keys "kind", and "data"
    """
    results = []
    c_json = comments_json.copy()
    for c in c_json:
        #test that this for loop keeps going on new objects added during the loop
        d = c['data']
        if c['kind'] == 'more':
            #print(d['children'][:5])
            #need to get_more_comments
            #get_more_comments will return a list of dicts, add that list to results
            c_json += get_more_comments(d['parent_id'],d['children'])
        else:
            #append a dict of info to our results list
            results.append({m:d[m] for m in metrics})
    return results

def get_more_comments(link_id,children):
    """
    return an additional comments object with more comments to parse
    """
    comms = []
    split_list = np.array_split(children,len(children) // 500) if len(children) >= 500 else children
    for child in split_list:
        #loop through chunks of 100 of the children array
        try:
            if isinstance(child,str) == True:
                #you are dealing with just one value
                c = child
            else:
                c = ",".join(child)
            request_string = "https://oauth.reddit.com/api/morechildren?link_id={}&children={}&limit_children=True&api_type=json".format(link_id,c)
            #print('pulling comments ',",".join(child))
            r = requests.get(request_string,headers=headers)#, params={'limit': '1000'})
            r = r.json()
            comms += r['json']['data']['things']
            #print('pulled comments ',c)
        except:
            print('error pulling child',child)
    return comms


#%%
#declare global vars for subreddits to query
SUBREDDIT_LIST = ('stocks',
                  'wallstreetbets',
                  'daytrading','investing','cryptocurrency',
                  'stockmarket',
                  )

#2 datasets. One that is post info and post ID
#Second dataset is post id and comment info
#Can join datasets together, keeps concise

all_posts = []
all_comments = []


#for each subreddit
for sub in SUBREDDIT_LIST:
    #Reauthenticate
    # send our request for an OAuth token
    res = requests.post('https://www.reddit.com/api/v1/access_token',
                        auth=auth, data=data, headers=headers)
    
    # convert response to JSON and pull access_token value
    TOKEN = res.json()['access_token']
    # TOKEN = res.json()
    
    # add authorization to our headers dictionary
    headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}
    
    # while the token is valid (~2 hours) we just add headers=headers to our requests
    requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)
    
    
    #append info about post
    last_post = "null" #begin with the argument for last post = null
    sub_posts = []
    for j in range(10):
        print(sub,j)
        url = "https://oauth.reddit.com/r/" + sub + "/top/?t=week&after={}".format(last_post)
        res = requests.get(url,headers=headers, params={'limit': '1000'})
    
        posts = get_results(res.json(),post_metrics)
        if len(posts) > 0:
            sub_posts.append(posts.copy())
            last_post = posts.iloc[-1]['name']
    
    posts = pd.concat(sub_posts)
    posts = posts.reset_index()
    all_posts.append(posts.copy())
    #for post in posts:
    for i in posts.index:
    #for i in posts.index[581:]:
        post_id = posts.at[i,'name'][3:] #(need to take off the first prefix of the post id)
        try:
            res_post = requests.get("https://oauth.reddit.com/r/" + sub + "/comments/" + post_id,
                           headers=headers, params={'limit': '1000'})
            r = res_post.json()
            #print(sub,post_id,'results pulled')
            post_info = r[0]
            comments = r[1]
            c_obj = comments['data']['children']
            comments_data = extract_comment_data(c_obj,comment_metrics)
            all_comments += comments_data.copy()
        except:
            print("error with post",post_id)
        #append info about comments
        
        #append data point of post, comment to final dataset
        
        
all_posts = pd.concat(all_posts)
all_comments = pd.DataFrame(all_comments)
all_comments.to_csv('all_comments_week_recent.csv',mode='a')
all_posts.to_csv('all_posts_week_week_recent.csv',mode='a')