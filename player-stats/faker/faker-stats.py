#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np  # linear algebra
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
import seaborn as sns

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os

for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All" 
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session


# In[2]:


# Display the entire dataframe
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 10)

# In[3]:


# Web scraping packages
from bs4 import BeautifulSoup
import requests

# # Faker Statistics

# In[4]:


url = "https://lol.fandom.com/wiki/Special:RunQuery/TournamentStatistics?TS%5Bpreload%5D=PlayerByChampion&TS" \
      "%5Btournament%5D=&TS%5Blink%5D=Faker&TS%5Bchampion%5D=&TS%5Brole%5D=&TS%5Bteam%5D=&TS%5Bpatch%5D=&TS%5Byear%5D" \
      "=&TS%5Bregion%5D=&TS%5Btournamentlevel%5D=&TS%5Bwhere%5D=&TS%5Bincludelink%5D%5Bis_checkbox%5D=true&TS" \
      "%5Bshownet%5D%5Bis_checkbox%5D=true&_run=&pfRunQueryFormName=TournamentStatistics&wpRunQuery=&pf_free_text= "

# In[5]:


page = requests.get(url)

# In[6]:


soup = BeautifulSoup(page.text, 'html5lib')

# In[7]:


faker_champ_stats_table = soup.find_all('table')[0]
faker_champ_stats_df = pd.DataFrame()

# In[8]:


temp = []
for tr in faker_champ_stats_table.tr.next_siblings:
    row = [td.text for td in tr]
    temp.append(row)
faker_champ_stats_df = pd.DataFrame(temp)

# In[9]:


faker_champ_stats_df

# In[10]:


faker_champ_stats_df.rename(columns=faker_champ_stats_df.iloc[1], inplace=True)

# In[11]:


faker_champ_stats_df.drop([0, 1], inplace=True)

# In[12]:


faker_champ_stats_df.drop([79, 80], inplace=True)

# In[13]:


faker_champ_stats_df.reset_index(drop=True, inplace=True)

# In[14]:


faker_champ_stats_df.columns = ['Champion', 'G', 'W', 'L', 'WR', 'K', 'D', 'A', 'KDA', 'CS', 'CS/M', 'Gold', 'G/M',
                                'DMG', 'DMG/M', 'KP', 'KS', 'GS']

# In[15]:


faker_champ_stats_df.head(10)

# In[16]:


faker_champ_stats_df.tail(10)

# This is a good start, but there are some missing stats. Let's try to fill in these missing stats manually. For now,
# let's use this as a temporary csv table.

# In[17]:


faker_champ_stats_df.to_csv('faker_champ_stats_temp.csv')

# Okay, so here I've used the `BeautifulSoup` package to scrape some data from the lol esports fandom wiki. There is
# no website I've found that just shows Faker's (or anyone elses) complete match history. Thus, I have to scrape from
# multiple tables and use a lot of dataframe joining to get the match history. It's not complete but I will have to
# do. There must be a way to piece together the information.
# 
# What I can do is get a list of tournaments Faker played in, then go to each of those tournaments, scrape the match
# history from those tournaments, and only look for Faker's games.
# 
# Actually, now that I think about it, I probably want to start by scraping the match history from every tournament
# ever. This way, I can filter the match history for certain teams and players so that things will be slightly easier
# in the future.
# 
# I plan to work on this a little bit every day. It may take a few years, but this seems like it'll be an interesting
# project.

# Also, a lot of missing data. Oof. Hopefully I can use tournament data to get the results.

# Welp, time to get the tournament data

# In[18]:


tournament_page = requests.get("https://lol.fandom.com/wiki/Faker/Tournament_Results")
soup_tournaments = BeautifulSoup(tournament_page.text, "html5lib")  # get the html

# In[19]:


tournaments = pd.read_html(tournament_page.text)[3]
tournaments

# In[20]:


tournaments = tournaments.droplevel(level=0, axis=1)

# I can't believe Faker has played in 70 tournaments. That's crazy. He's the GOAT for a reason.

# In[21]:


# list of tournaments to scrape data from
tournaments.columns

# In[22]:


tournaments['index'] = range(len(tournaments), 0, -1)
tournaments.rename(columns={'index': 'Tournament Number'}, inplace=True)

# In[23]:


standings = tournaments.loc[:, 'Last Result']
standing_number = 0
for standing in standings:
    index = 0
    for ch in standing:
        if ord(ch) >= 65 and ord(ch) <= 90:
            standings[standing_number] = standing[:index] + " " + standing[index:]
            break
        index += 1
    standing_number += 1
standings = standings.to_numpy()
count = 0
for standing in standings:
    standing = standing.encode('ascii', 'ignore').decode('utf-8').strip()
    # print(standing)
    temp = standing.split()
    standing = ' '.join(temp)
    standings[count] = standing
    count += 1

# In[24]:


tournaments['Last Result'] = standings
tournaments

# In[25]:


tournaments.to_csv("faker_results_tournaments.csv")

# In[26]:


FAKER_GAMES_PLAYED = np.sum(faker_champ_stats_df['G'].astype(int).to_numpy())
FAKER_GAMES_PLAYED

# In[27]:


FAKER_GAMES_WON = np.sum(faker_champ_stats_df['W'].astype(int).to_numpy())
FAKER_GAMES_WON

# In[28]:


FAKER_OVERALL_WINRATE = FAKER_GAMES_WON / FAKER_GAMES_PLAYED
FAKER_OVERALL_WINRATE


# Unfortunately, it seems there is no match history for the first tournament Faker played, the *Champions 2013 Spring Qualifiers*, so we will have to work without it. Luckily, we can scrape data from the next event, the *Champions 2013 Spring* tournament.

# In[29]:


def get_html_table(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')
    table = soup.find_all('table')[0]
    return table


# In[30]:


def get_tournament_df(table):
    temp = []
    for tr in table.tr.next_siblings:
        row = []
        for td in tr:
            anchors = td.find_all('a')
            spans = td.find_all('span')
            # print(anchors)
            if anchors:
                title = anchors[0].get('title')
                if title:
                    row.append(title)
            elif spans:
                if len(spans) == 1:
                    title = spans[0].get('title')
                    if title:
                        row.append(title)
                    else:
                        row.append(td.text)
                else:
                    lst = []
                    for span in spans:
                        title = span.get('title')
                        if title:
                            lst.append(title)
                    if lst:
                        row.append(lst)
                    else:
                        row.append(td.text)
            else:
                if td.text != "":
                    row.append(td.text)
                else:
                    row.append(pd.NA)
        temp.append(row)
    df = pd.DataFrame(temp)
    df.loc[1, 6] = 'OpponentTeam'

    df.rename(columns=df.iloc[1], inplace=True)
    df.drop(index=[0, 1, 2], inplace=True)
    df.rename(columns={'ΔCS': 'CSD'}, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.drop(index=[len(df.index) - 1], inplace=True)
    csd = df['CSD']
    new_csd = []
    for st in csd:
        st = st.replace('\u25bc', '-').replace('\u25b2', '').replace('\u25ac', '0')
        new_csd.append(int(st))
    df['CSD'] = new_csd
    df['CSD'] = df['CSD'].astype(int)
    df['SpellD'] = df['Spells'].map(lambda x: x[0])
    df['SpellF'] = df['Spells'].map(lambda x: x[1])
    df['K'] = df['K'].astype(int)
    df['D'] = df['D'].astype(int)
    df['A'] = df['A'].astype(int)
    df['G'] = pd.to_numeric(df['G'], errors='coerce').fillna(pd.NA)
    df['KDA'] = df[['K', 'D', 'A']].apply(
        func=(lambda x: (x['K'] + x['A']) / x['D'] if x['D'] > 0 else x['K'] + x['A']), axis=1)
    df['KDA'] = np.round(df['KDA'], decimals=2)
    df['Item1'] = df['Items'].map(lambda x: x[0])
    df['Item2'] = df['Items'].map(lambda x: x[1])
    df['Item3'] = df['Items'].map(lambda x: x[2])
    df['Item4'] = df['Items'].map(lambda x: x[3])
    df['Item5'] = df['Items'].map(lambda x: x[4])
    df['Item6'] = df['Items'].map(lambda x: x[5])
    df[['Blue', 'Red']] = df[['Side', 'Team', 'OpponentTeam']].apply(
        func=(lambda row: [row[1], row[2]] if row[0] == 'Blue' else [row[2], row[1]]), axis=1, result_type='expand')

    df.drop(columns=['Spells', 'P', 'SB', 'VOD'], inplace=True)

    df = df[
        ['Date', 'Tournament', 'Team', 'OpponentTeam', 'W/L', 'Blue', 'Red', 'Side', 'Len', 'C', 'Vs', 'K', 'D', 'A',
         'KDA', 'CS', 'G', 'Dmg', 'CSD', 'SpellD', 'SpellF', 'Items', 'Item1', 'Item2', 'Item3', 'Item4', 'Item5',
         'Item6']]
    df.rename(columns={'Len': 'Length', 'C': 'Champion', 'G': 'Gold(thousand)'}, inplace=True)

    return df


# In[31]:


url = "https://lol.fandom.com/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions%202013%20Spring&MHP%5Bspl%5D=yes&MHP%5Blink%5D=Faker&_run="

# In[32]:


table = get_html_table(url)
faker_2013_spring = get_tournament_df(table)
faker_2013_spring

# In[33]:


faker_2013_spring.to_csv('faker_2013_spring.csv')

# In[34]:


url = "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions+2013+Summer&MHP%5Blink%5D=Faker&_run="

# In[35]:


table = get_html_table(url)
faker_2013_summer = get_tournament_df(table)
faker_2013_summer

# In[36]:


faker_2013_summer.to_csv('faker_2013_summer.csv')

# In[37]:


url = "https://lol.fandom.com/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Korea%20Regional%20Finals%20Season%203&MHP%5Bspl%5D=yes&MHP%5Blink%5D=Faker&_run="

# In[38]:


table = get_html_table(url)
faker_2013_regional_finals = get_tournament_df(table)
faker_2013_regional_finals

# In[39]:


faker_2013_regional_finals.to_csv('faker_2013_regional_finals.csv')

# In[40]:


url = 'https://lol.fandom.com/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=World%20Championship%20Season%203&MHP%5Bspl%5D=yes&MHP%5Blink%5D=Faker&_run='

# In[41]:


table = get_html_table(url)
faker_2013_worlds = get_tournament_df(table)
faker_2013_worlds

# In[42]:


faker_2013_worlds.to_csv('faker_2013_worlds.csv')

# In[43]:


url = "https://lol.fandom.com/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions%202014%20Winter&MHP%5Bspl%5D=yes&MHP%5Blink%5D=Faker&_run="

# In[44]:


table = get_html_table(url)
faker_2014_winter = get_tournament_df(table)
faker_2014_winter

# In[45]:


faker_2014_winter.to_csv('faker_2014_winter.csv')

# In[46]:


url = "https://lol.fandom.com/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions%202014%20Spring&MHP%5Bspl%5D=yes&MHP%5Blink%5D=Faker&_run="

# In[47]:


table = get_html_table(url)
faker_2014_spring = get_tournament_df(table)
faker_2014_spring

# In[48]:


faker_2014_spring.to_csv('faker_2014_spring.csv')

# In[49]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=All-Star+2014+Paris&MHP%5Blink%5D=Faker&_run='

# In[50]:


table = get_html_table(url)
faker_2014_all_stars = get_tournament_df(table)
faker_2014_all_stars

# In[51]:


faker_2014_all_stars.to_csv('faker_2014_all_stars.csv')

# In[52]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=NLB+2014+Summer&MHP%5Blink%5D=Faker&_run='

# In[53]:


table = get_html_table(url)
faker_2014_nlb_summer = get_tournament_df(table)
faker_2014_nlb_summer

# In[54]:


faker_2014_nlb_summer.to_csv('faker_2014_nlb_summer.csv')

# In[55]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions+2014+Summer&MHP%5Blink%5D=Faker&_run='

# In[56]:


table = get_html_table(url)
faker_2014_summer = get_tournament_df(table)
faker_2014_summer

# In[57]:


faker_2014_summer.to_csv('faker_2014_summer.csv')

# In[58]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Korea+Regional+Finals+2014&MHP%5Blink%5D=Faker&_run='

# In[59]:


table = get_html_table(url)
faker_2014_regional_finals = get_tournament_df(table)
faker_2014_regional_finals

# In[60]:


faker_2014_regional_finals.to_csv('faker_2014_regional_finals.csv')

# In[61]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions+2015+Spring+Preseason&MHP%5Blink%5D=Faker&_run='

# In[62]:


table = get_html_table(url)
faker_2015_preseason = get_tournament_df(table)
faker_2015_preseason

# In[63]:


faker_2015_preseason.to_csv('faker_2015_preseason.csv')

# In[64]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=Champions+2015+Spring&MHP%5Bshowstats%5D=2015&_run='
table = get_html_table(url)
faker_2015_spring = get_tournament_df(table)
faker_2015_spring

# In[65]:


faker_2015_spring.to_csv('faker_2015_spring.csv')

# In[66]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions+2015+Spring+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2015_spring_playoffs = get_tournament_df(table)
faker_2015_spring_playoffs

# In[67]:


faker_2015_spring_playoffs.to_csv('faker_2015_spring_playoffs.csv')

# In[68]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=MSI+2015&MHP%5Bshowstats%5D=2015&_run='
table = get_html_table(url)
faker_2015_msi = get_tournament_df(table)
faker_2015_msi

# In[69]:


faker_2015_msi.to_csv('faker_2015_msi.csv')

# In[70]:


url = 'https://lol.fandom.com/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Champions%202015%20Summer&MHP%5Bspl%5D=yes&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2015_summer = get_tournament_df(table)
faker_2015_summer

# In[71]:


faker_2015_summer.to_csv('faker_2015_summer.csv')

# In[72]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=Champions+2015+Summer+Playoffs&MHP%5Bshowstats%5D=2015&_run='
table = get_html_table(url)
faker_2015_summer_playoffs = get_tournament_df(table)
faker_2015_summer_playoffs

# In[73]:


faker_2015_summer_playoffs.to_csv('faker_2015_summer_playoffs.csv')

# In[74]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=World+Championship+2015&MHP%5Bshowstats%5D=2015&_run='
table = get_html_table(url)
faker_2015_worlds = get_tournament_df(table)
faker_2015_worlds

# In[75]:


faker_2015_worlds.to_csv('faker_2015_worlds.csv')

# In[76]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=KeSPA+Cup+2015&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2015_kespa = get_tournament_df(table)
faker_2015_kespa

# In[77]:


faker_2015_kespa.to_csv('faker_2015_kespa.csv')

# In[78]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=IEM+Season+10+World+Championship&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2016_iem = get_tournament_df(table)
faker_2016_iem

# In[79]:


faker_2016_iem.to_csv('faker_2016_iem.csv')

# In[80]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2016+Spring&MHP%5Bshowstats%5D=2016&_run='
table = get_html_table(url)
faker_2016_spring = get_tournament_df(table)
faker_2016_spring

# In[81]:


faker_2016_spring.to_csv('faker_2016_spring.csv')

# In[82]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2016+Spring+Playoffs&MHP%5Bshowstats%5D=2016&_run='
table = get_html_table(url)
faker_2016_spring_playoffs = get_tournament_df(table)
faker_2016_spring_playoffs

# In[83]:


faker_2016_spring_playoffs.to_csv('faker_2016_spring_playoffs.csv')

# In[84]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=MSI+2016&MHP%5Bshowstats%5D=2016&_run='
table = get_html_table(url)
faker_2016_msi = get_tournament_df(table)
faker_2016_msi

# In[85]:


faker_2016_msi.to_csv('faker_2016_msi.csv')

# In[86]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2016+Summer&MHP%5Bshowstats%5D=2016&_run='
table = get_html_table(url)
faker_2016_summer = get_tournament_df(table)
faker_2016_summer

# In[87]:


faker_2016_summer.to_csv('faker_2016_summer.csv')

# In[88]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2016+Summer+Playoffs&MHP%5Bshowstats%5D=2016&_run='
table = get_html_table(url)
faker_2016_summer_playoffs = get_tournament_df(table)
faker_2016_summer_playoffs

# In[89]:


faker_2016_summer_playoffs.to_csv('faker_2016_summer_playoffs.csv')

# In[90]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=World+Championship+2016&MHP%5Bshowstats%5D=2016&_run='
table = get_html_table(url)
faker_2016_worlds = get_tournament_df(table)
faker_2016_worlds

# In[91]:


faker_2016_worlds.to_csv('faker_2016_worlds.csv')

# In[92]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=KeSPA+Cup+2016&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2016_kespa = get_tournament_df(table)
faker_2016_kespa

# In[93]:


faker_2016_kespa.to_csv('faker_2016_kespa.csv')

# In[94]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2017+Spring&MHP%5Bshowstats%5D=2017&_run='
table = get_html_table(url)
faker_2017_spring = get_tournament_df(table)
faker_2017_spring

# In[95]:


faker_2017_spring.to_csv('faker_2017_spring.csv')

# In[96]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2017+Spring+Playoffs&MHP%5Bshowstats%5D=2017&_run='
table = get_html_table(url)
faker_2017_spring_playoffs = get_tournament_df(table)
faker_2017_spring_playoffs

# In[97]:


faker_2017_spring_playoffs.to_csv('faker_2017_spring_playoffs.csv')

# In[98]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Bno-cat%5D=true&MHP%5Bshowstats%5D=2017&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=MSI+2017+Play-In%2C+MSI+2017+Main+Event&_run='
table = get_html_table(url)
faker_2017_msi = get_tournament_df(table)
faker_2017_msi

# In[99]:


faker_2017_msi.to_csv('faker_2017_msi.csv')

# In[100]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=Rift+Rivals+2017+LCK-LPL-LMS&MHP%5Bshowstats%5D=2017&_run='
table = get_html_table(url)
faker_2017_rift_rivals = get_tournament_df(table)
faker_2017_rift_rivals

# In[101]:


faker_2017_rift_rivals.to_csv('faker_2017_rift_rivals.csv')

# In[102]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2017+Summer&MHP%5Bshowstats%5D=2017&_run='
table = get_html_table(url)
faker_2017_summer = get_tournament_df(table)
faker_2017_summer

# In[103]:


faker_2017_summer.to_csv('faker_2017_summer.csv')

# In[104]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2017+Summer+Playoffs&MHP%5Bshowstats%5D=2017&_run='
table = get_html_table(url)
faker_2017_summer_playoffs = get_tournament_df(table)
faker_2017_summer_playoffs

# In[105]:


faker_2017_summer_playoffs.to_csv('faker_2017_summer_playoffs.csv')

# In[106]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=Worlds+2017+Main+Event&MHP%5Bshowstats%5D=2017&_run='
table = get_html_table(url)
faker_2017_worlds = get_tournament_df(table)
faker_2017_worlds

# In[107]:


faker_2017_worlds.to_csv('faker_2017_worlds.csv')

# In[108]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=KeSPA+Cup+2017&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2017_kespa = get_tournament_df(table)
faker_2017_kespa

# In[109]:


faker_2017_kespa.to_csv('faker_2017_kespa.csv')

# In[110]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=All-Star+2017+Los+Angeles&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2017_all_stars = get_tournament_df(table)
faker_2017_all_stars

# In[111]:


faker_2017_all_stars.to_csv('faker_2017_all_stars.csv')

# In[112]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2018+Spring&MHP%5Bshowstats%5D=2018&_run='
table = get_html_table(url)
faker_2018_spring = get_tournament_df(table)
faker_2018_spring

# In[113]:


faker_2018_spring.to_csv('faker_2018_spring.csv')

# In[114]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2018+Spring+Playoffs&MHP%5Bshowstats%5D=2018&_run='
table = get_html_table(url)
faker_2018_spring_playoffs = get_tournament_df(table)
faker_2018_spring_playoffs

# In[115]:


faker_2018_spring_playoffs.to_csv('faker_2018_spring_playoffs.csv')

# In[116]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Asian+Games+2018+Q+-+EA&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2018_asian_games = get_tournament_df(table)
faker_2018_asian_games

# In[117]:


faker_2018_asian_games.to_csv('faker_2018_asian_games.csv')

# In[118]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=Rift+Rivals+2018+LCK-LPL-LMS&MHP%5Bshowstats%5D=2018&_run='
table = get_html_table(url)
faker_2018_rift_rivals = get_tournament_df(table)
faker_2018_rift_rivals

# In[119]:


faker_2018_rift_rivals.to_csv('faker_2018_rift_rivals.csv')

# In[120]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2018+Summer&MHP%5Bshowstats%5D=2018&_run='
table = get_html_table(url)
faker_2018_summer = get_tournament_df(table)
faker_2018_summer

# In[121]:


faker_2018_summer.to_csv('faker_2018_summer.csv')

# In[122]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=Korea+Regional+Finals+2018&MHP%5Bshowstats%5D=2018&_run='
table = get_html_table(url)
faker_2018_regional_finals = get_tournament_df(table)
faker_2018_regional_finals

# In[123]:


faker_2018_regional_finals.to_csv('faker_2018_regional_finals.csv')

# In[124]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=KeSPA+Cup+2018&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2018_kespa_cup = get_tournament_df(table)
faker_2018_kespa_cup

# In[125]:


faker_2018_kespa_cup.to_csv('faker_2018_kespa_cup.csv')

# In[126]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2019+Spring&MHP%5Bshowstats%5D=2019&_run='
table = get_html_table(url)
faker_2019_spring = get_tournament_df(table)
faker_2019_spring

# In[127]:


faker_2019_spring.to_csv('faker_2019_spring.csv')

# In[128]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Blink%5D=Faker&MHP%5Btournament%5D=LCK+2019+Spring+Playoffs&MHP%5Bshowstats%5D=2019&_run='
table = get_html_table(url)
faker_2019_spring_playoffs = get_tournament_df(table)
faker_2019_spring_playoffs

# In[129]:


faker_2019_spring_playoffs.to_csv('faker_2019_spring_playoffs.csv')

# In[130]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=MSI+2019+Play-In%2C+MSI+2019+Main+Event&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2019_msi = get_tournament_df(table)
faker_2019_msi

# In[131]:


faker_2019_msi.to_csv('faker_2019_msi.csv')

# In[132]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=Rift+Rivals+2019+LCK-LPL-LMS-VCS&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2019_rift_rivals = get_tournament_df(table)
faker_2019_rift_rivals

# In[133]:


faker_2019_rift_rivals.to_csv('faker_2019_rift_rivals.csv')

# In[134]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK+2019+Summer&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2019_summer = get_tournament_df(table)
faker_2019_summer

# In[135]:


faker_2019_summer.to_csv('faker_2019_summer.csv')

# In[136]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2019+Season%2FSummer+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2019_summer_playoffs = get_tournament_df(table)
faker_2019_summer_playoffs

# In[137]:


faker_2019_summer_playoffs.to_csv('faker_2019_summer_playoffs.csv')

# In[138]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=2019+Season+World+Championship%2FMain+Event%2C2019+Season+World+Championship%2FPlay-In&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2019_worlds = get_tournament_df(table)
faker_2019_worlds

# In[139]:


faker_2019_worlds.to_csv('faker_2019_worlds.csv')

# In[140]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=2019+LoL+KeSPA+Cup&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2019_kespa_cup = get_tournament_df(table)
faker_2019_kespa_cup

# In[141]:


faker_2019_kespa_cup.to_csv('faker_2019_kespa_cup.csv')

# In[142]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2020+Season%2FSpring+Season&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2020_spring = get_tournament_df(table)
faker_2020_spring

# In[143]:


faker_2020_spring.to_csv('faker_2020_spring.csv')

# In[144]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2020+Season%2FSpring+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2020_spring_playoffs = get_tournament_df(table)
faker_2020_spring_playoffs

# In[145]:


faker_2020_spring_playoffs.to_csv('faker_2020_spring_playoffs.csv')

# In[146]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=2020+Mid-Season+Cup&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2020_midseason_cup = get_tournament_df(table)
faker_2020_midseason_cup

# In[147]:


faker_2020_midseason_cup.to_csv('faker_2020_midseason_cup.csv')

# In[148]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2020+Season%2FSummer+Season&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2020_summer = get_tournament_df(table)
faker_2020_summer

# In[149]:


faker_2020_summer.to_csv('faker_2020_summer.csv')

# In[150]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2020+Season%2FSummer+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2020_summer_playoffs = get_tournament_df(table)
faker_2020_summer_playoffs

# In[151]:


faker_2020_summer_playoffs.to_csv('faker_2020_summer_playoffs.csv')

# In[152]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2020+Season%2FRegional+Finals&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2020_regional_finals = get_tournament_df(table)
faker_2020_regional_finals

# In[153]:


faker_2020_regional_finals.to_csv('faker_2020_regional_finals.csv')

# In[154]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2021+Season%2FSpring+Season&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2021_spring = get_tournament_df(table)
faker_2021_spring

# In[155]:


faker_2021_spring.to_csv('faker_2021_spring.csv')

# In[156]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2021+Season%2FSpring+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2021_spring_playoffs = get_tournament_df(table)
faker_2021_spring_playoffs

# In[157]:


faker_2021_spring_playoffs.to_csv('faker_2021_spring_playoffs.csv')

# In[158]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2021+Season%2FSummer+Season&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2021_summer = get_tournament_df(table)
faker_2021_summer

# In[159]:


faker_2021_summer.to_csv('faker_2021_summer.csv')

# In[160]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2021+Season%2FSummer+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2021_summer_playoffs = get_tournament_df(table)
faker_2021_summer_playoffs

# In[161]:


faker_2021_summer_playoffs.to_csv('faker_2021_summer_playoffs.csv')

# In[162]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2021+Season%2FRegional+Finals&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2021_regional_finals = get_tournament_df(table)
faker_2021_regional_finals

# In[163]:


faker_2021_regional_finals.to_csv('faker_2021_regional_finals.csv')

# In[164]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=2021+Season+World+Championship%2FMain+Event%2C2021+Season+World+Championship%2FPlay-In&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2021_worlds = get_tournament_df(table)
faker_2021_worlds

# In[165]:


faker_2021_worlds.to_csv('faker_2021_worlds.csv')

# In[166]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2022+Season%2FSpring+Season&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2022_spring = get_tournament_df(table)
faker_2022_spring

# In[167]:


faker_2022_spring.to_csv('faker_2022_spring.csv')

# In[168]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2022+Season%2FSpring+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2022_spring_playoffs = get_tournament_df(table)
faker_2022_spring_playoffs

# In[169]:


faker_2022_spring_playoffs.to_csv('faker_2022_spring_playoffs.csv')

# In[170]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=2022+Mid-Season+Invitational&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2022_msi = get_tournament_df(table)
faker_2022_msi

# In[171]:


faker_2022_msi.to_csv('faker_2022_msi.csv')

# In[172]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2022+Season%2FSummer+Season&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2022_summer = get_tournament_df(table)
faker_2022_summer

# In[173]:


faker_2022_summer.to_csv('faker_2022_summer.csv')

# In[174]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=LCK%2F2022+Season%2FSummer+Playoffs&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2022_summer_playoffs = get_tournament_df(table)
faker_2022_summer_playoffs

# In[175]:


faker_2022_summer_playoffs.to_csv('faker_2022_summer_playoffs.csv')

# In[176]:


url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryPlayer?MHP%5Bpreload%5D=Player&MHP%5Btournament%5D=2022+Season+World+Championship%2FMain+Event%2C2022+Season+World+Championship%2FPlay-In&MHP%5Blink%5D=Faker&_run='
table = get_html_table(url)
faker_2022_worlds = get_tournament_df(table)
faker_2022_worlds

# In[177]:


faker_2022_worlds.to_csv('faker_2022_worlds.csv')

# In[178]:


PATH = '/kaggle/working'
END_CSV = '.csv'
START = 'faker_20'
all_faker_csvs = os.listdir(PATH)
all_faker_csvs = list(filter(lambda file: file.endswith(END_CSV) and file.startswith(START), all_faker_csvs))
all_faker_csvs

# In[179]:


faker_match_history = pd.concat(
    map(pd.read_csv, all_faker_csvs), ignore_index=True)

# In[180]:


faker_match_history

# In[181]:


faker_match_history.sort_values(by=['Date', 'Unnamed: 0'], ascending=[False, True], inplace=True)

# In[182]:


faker_match_history = faker_match_history.reset_index(drop=True)
faker_match_history

# In[183]:


faker_match_history.to_csv('faker_match_history.csv')

# There's a null game length, so we have to fix that.

# In[184]:


faker_match_history[faker_match_history['Length'].isnull()]

# In[185]:


avg_min = np.mean(faker_match_history['Length'].dropna().str.split(':').str[0].astype(int))
faker_match_history['min'] = faker_match_history['Length'].str.split(':').str[0].fillna(avg_min).astype(float)
faker_match_history['min']

# In[186]:


avg_sec = np.mean(faker_match_history['Length'].dropna().str.split(':').str[1].astype(int))
faker_match_history['sec'] = faker_match_history['Length'].str.split(':').str[1].fillna(avg_min).astype(float)
faker_match_history['sec']

# In[187]:


faker_match_history['time_seconds'] = faker_match_history['min'] * 60 + faker_match_history['sec']
faker_match_history['time_seconds']

# Also, the damage chart has some NaN values, so we have to deal with that too.

# In[188]:


sum(faker_match_history['Dmg'].isnull())

# In[189]:


groupby_func = {'W/L': (lambda x: np.count_nonzero(x == 'Win')), 'K': 'sum', 'D': 'sum', 'A': 'sum', 'CSD': np.nanmean,
                'CS': 'sum', 'Champion': 'count', 'time_seconds': 'sum', 'Gold(thousand)': 'sum', 'Dmg': (
        lambda x: np.nan_to_num(np.round(np.nanmean(x), 3) * 1000).astype(int) if sum(x.isnull()) != len(x) else pd.NA)}

# In[190]:


faker_champ_stats = faker_match_history[
    ['Champion', 'W/L', 'K', 'D', 'A', 'CSD', 'CS', 'time_seconds', 'Gold(thousand)', 'Dmg']].groupby('Champion').agg(
    func=groupby_func)

# In[191]:


faker_champ_stats

# In[192]:


faker_champ_stats = faker_champ_stats.rename({'Champion': 'Games'}, axis=1)

# In[193]:


faker_champ_stats['WR'] = faker_champ_stats['W/L'] / faker_champ_stats['Games']
faker_champ_stats['WR']

# In[194]:


faker_champ_stats['CS/M'] = faker_champ_stats['CS'] / faker_champ_stats['time_seconds'] * 60
faker_champ_stats['CS/M']

# In[195]:


faker_champ_stats['Gold/M'] = faker_champ_stats['Gold(thousand)'] / faker_champ_stats['time_seconds'] * 60 * 1000
faker_champ_stats['Gold/M']

# In[196]:


kda_func = lambda x: (x['K'] + x['A']) / x['D'] if x['D'] > 0 else x['K'] + x['A']

# In[197]:


faker_champ_stats['KDA'] = faker_champ_stats[['K', 'D', 'A']].apply(func=kda_func, axis=1)
faker_champ_stats['KDA']

# In[198]:


faker_champ_stats

# In[199]:


faker_champ_stats = faker_champ_stats.replace(np.NaN, pd.NA)

# In[200]:


faker_champ_stats

# In[201]:


faker_champ_stats['K'] = faker_champ_stats['K'] / faker_champ_stats['Games']
faker_champ_stats['D'] = faker_champ_stats['D'] / faker_champ_stats['Games']
faker_champ_stats['A'] = faker_champ_stats['A'] / faker_champ_stats['Games']
faker_champ_stats['time_seconds'] = faker_champ_stats['time_seconds'] / faker_champ_stats['Games']

# In[202]:


temp1 = np.round(faker_champ_stats['time_seconds'] // 60, 1).astype(int)
temp2 = np.round(faker_champ_stats['time_seconds'] % 60, 1).astype(int)
buffer1 = temp2.astype(str).where(temp2.astype(int) >= 10, '0' + temp2.astype(str))
faker_champ_stats['Average Game Time'] = temp1.astype(str) + ":" + buffer1

# In[203]:


faker_champ_stats = faker_champ_stats.rename({'W/L': 'Wins', 'CSD': 'Average CSD', 'Dmg': 'Average Dmg'}, axis=1)

# In[204]:


faker_champ_stats = faker_champ_stats[
    ['Games', 'Wins', 'WR', 'K', 'D', 'A', 'KDA', 'Average CSD', 'Average Dmg', 'CS/M', 'Gold/M', 'Average Game Time']]
faker_champ_stats

# In[205]:


faker_champ_stats['WR'] = np.round(faker_champ_stats['WR'] * 100, 1).astype(str) + '%'
faker_champ_stats

# In[206]:


faker_champ_stats['K'] = np.round(faker_champ_stats['K'], 1)
faker_champ_stats['K']

# In[207]:


faker_champ_stats['D'] = np.round(faker_champ_stats['D'], 1)
faker_champ_stats['D']

# In[208]:


faker_champ_stats['A'] = np.round(faker_champ_stats['A'], 1)
faker_champ_stats['A']

# In[209]:


faker_champ_stats['Average CSD'] = np.round(faker_champ_stats['Average CSD'], 1)
faker_champ_stats['Average CSD']

# In[210]:


faker_champ_stats['CS/M'] = np.round(faker_champ_stats['CS/M'], 2)
faker_champ_stats['CS/M']

# In[211]:


faker_champ_stats['Gold/M'] = np.round(faker_champ_stats['Gold/M'], 1)
faker_champ_stats['Gold/M']

# In[212]:


faker_champ_stats['KDA'] = np.round(faker_champ_stats['KDA'], 2)
faker_champ_stats['KDA']

# In[213]:


faker_champ_stats

# In[214]:


faker_champ_stats.to_csv('faker_champ_stats.csv')

# In[ ]:


# In[215]:


temp = faker_champ_stats['Wins'] / faker_champ_stats['Games'] * 100
wr_hist = sns.histplot(x=temp, stat='density', bins=20)

# In[216]:


fig = wr_hist.get_figure()
fig.savefig("faker_wr_hist.jpg")

# In[ ]:
