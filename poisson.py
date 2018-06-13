import operator
import math
import pandas as pd
import xlsxwriter
import numpy as np
import random
import operator

def get_world_cup_teams(team_elo):
    worldcup_elo = {}
    sheet = pd.read_csv('src/participatingteams.csv')
    for i, sheet_row in sheet.iterrows():
        team = sheet_row['Teams']
        group = sheet_row['Group']
        # off score, def score, group, seed in group
        worldcup_elo[team] = (team_elo[team][1], team_elo[team][2], group[0], i) #int(group[1
    return worldcup_elo

def print_scores(workbook, worldcup_elo):
    BOLD = workbook.add_format({'bold': True})
    worksheet = workbook.add_worksheet('ELO Scores')
    row, col = 1, 0

    worksheet.write(0,0, 'Team', BOLD)
    worksheet.write(0,1, 'Group', BOLD)
    worksheet.write(0,2, 'Off Score', BOLD)
    worksheet.write(0,3, 'Def Score', BOLD)
    for team in worldcup_elo:
        worksheet.write(row, col, team)
        worksheet.write(row, col+1, worldcup_elo[team][2])
        worksheet.write(row, col+2, worldcup_elo[team][0])
        worksheet.write(row, col+3, worldcup_elo[team][1])
        row+=1
    return worldcup_elo

def get_results_matrix(worldcup_elo):
    n = 496
    m = 23
    resultsMatrix = [[""] * m for i in range(n)]

    row = 0
    for t1 in worldcup_elo:
        for t2 in worldcup_elo:
            t1_off, t1_def, t1_group, t1_num = worldcup_elo[t1]
            t2_off, t2_def, t2_group, t2_num = worldcup_elo[t2]
            if t1==t2 or t1_num > t2_num:
                continue
            t1_xG = 1.35*t1_off/t2_def
            t2_xG = 1.35*t2_off/t1_def

            resultsMatrix[row][0] = t1_group
            resultsMatrix[row][1] = t2_group
            resultsMatrix[row][2] = t1
            resultsMatrix[row][3] = t2
            resultsMatrix[row][4] = t1_xG
            resultsMatrix[row][5] = t2_xG

            p_sum_t1 = 0
            p_sum_t2 = 0
            for x in range(0, 6):
                p_t1_xGoals = (t1_xG**x) * (np.exp(1)**(-1*t1_xG)) / math.factorial(x)
                p_t2_xGoals = (t2_xG**x) * (np.exp(1)**(-1*t2_xG)) / math.factorial(x)
                resultsMatrix[row][6 + x] = p_t1_xGoals
                resultsMatrix[row][13 + x] = p_t2_xGoals
                p_sum_t1+=p_t1_xGoals
                p_sum_t2+=p_t2_xGoals

            resultsMatrix[row][12] = 1 - p_sum_t1
            resultsMatrix[row][19] = 1 - p_sum_t2

            probWin = 0
            probDraw = 0
            probLoss = 0
            # probability of draw
            for x in range(0, 7):
                probDraw+=(resultsMatrix[row][6 + x] * resultsMatrix[row][13 + x])
            #probability of win
            for x in range(0, 7):
                for y in range(0, x):
                    probWin+=(resultsMatrix[row][6 + x] * resultsMatrix[row][13 + y])
            #probability of loss
            for x in range(0, 7):
                for y in range(6, x, -1):
                    probLoss+=(resultsMatrix[row][6 + x] * resultsMatrix[row][13 + y])

            resultsMatrix[row][20] = probWin
            resultsMatrix[row][21] = probDraw
            resultsMatrix[row][22] = probLoss
            row+=1
    return resultsMatrix

def print_match_prediction_labels(worksheet, BOLD):
    worksheet.write(0,0, 'Group: 1', BOLD)
    worksheet.write(0,1, 'Group: 2', BOLD)
    worksheet.write(0,2, 'Team 1', BOLD)
    worksheet.write(0,3, 'Team 2', BOLD)
    worksheet.write(0,4, 'xG1', BOLD)
    worksheet.write(0,5, 'xG2', BOLD)

    worksheet.write(0,6, 'P(T1_0G)', BOLD)
    worksheet.write(0,7, 'P(T1_1G)', BOLD)
    worksheet.write(0,8, 'P(T1_2G)', BOLD)
    worksheet.write(0,9, 'P(T1_3G)', BOLD)
    worksheet.write(0,10, 'P(T1_4G)', BOLD)
    worksheet.write(0,11, 'P(T1_5G)', BOLD)
    worksheet.write(0,12, 'P(T1_6G+)', BOLD)

    worksheet.write(0,13, 'P(T2_0G)', BOLD)
    worksheet.write(0,14, 'P(T2_1G)', BOLD)
    worksheet.write(0,15, 'P(T2_2G)', BOLD)
    worksheet.write(0,16, 'P(T2_3G)', BOLD)
    worksheet.write(0,17, 'P(T2_4G)', BOLD)
    worksheet.write(0,18, 'P(T2_5G)', BOLD)
    worksheet.write(0,19, 'P(T2_6G+)', BOLD)
    worksheet.write(0,20, 'P(T1 Wins', BOLD)
    worksheet.write(0,21, 'P(Draw)', BOLD)
    worksheet.write(0,22, 'P(T2 Wins)', BOLD)

def print_match_predictions(worksheet, worldcup_elo):
    resultsMatrix = get_results_matrix(worldcup_elo)
    num_rows = len(resultsMatrix)
    num_cols = len(resultsMatrix[0])

    for row in range(0, num_rows):
        for col in range(0, num_cols):
            worksheet.write(row + 1, col, resultsMatrix[row][col])
    return resultsMatrix

def create_sim_matrix(resultsMatrix):

    simulate_matrix = []

    for row in range(0, len(resultsMatrix)):
        if resultsMatrix[row][0] != resultsMatrix[row][1]:
            continue
        dict = {}
        dict['Team 1'] = resultsMatrix[row][2]
        dict['Team 2'] = resultsMatrix[row][3]
        dict['P(T1_0G)'] = resultsMatrix[row][6]
        dict['P(T1_1G)'] = resultsMatrix[row][7]
        dict['P(T1_2G)'] = resultsMatrix[row][8]
        dict['P(T1_3G)'] = resultsMatrix[row][9]
        dict['P(T1_4G)'] = resultsMatrix[row][10]
        dict['P(T1_5G)'] = resultsMatrix[row][11]
        dict['P(T1_6G)'] = resultsMatrix[row][12]
        dict['P(T2_0G)'] = resultsMatrix[row][13]
        dict['P(T2_1G)'] = resultsMatrix[row][14]
        dict['P(T2_2G)'] = resultsMatrix[row][15]
        dict['P(T2_3G)'] = resultsMatrix[row][16]
        dict['P(T2_4G)'] = resultsMatrix[row][17]
        dict['P(T2_5G)'] = resultsMatrix[row][18]
        dict['P(T2_6G)'] = resultsMatrix[row][19]
        simulate_matrix.append(dict)
    return simulate_matrix

def rankTeams(myGroup):
    myList = []
    t1 = ""
    t2 = ""
    t3 = ""
    t4 = ""
    teamNum = 1
    for team in myGroup:
        if teamNum == 1:
            t1 = team
        elif teamNum == 2:
            t2 = team
        elif teamNum == 3:
            t3 = team
        elif teamNum == 4:
            t4 = team
        else:
            raise Exception('Team error')
        gf, ga, gd, pts = myGroup[team]
        myList.append((team, gf, ga, gd, pts))
        teamNum += 1

    sortedList = sorted(myList, key = operator.itemgetter(4, 3, 1, 0))[::-1]
    return sortedList

def simulate_games(myMatrix):

    #myGroup = {'Team Name': gf, ga, gd, points)
    #e.g. {'Saudi Arabia': (1, 2, -1, 0)}
    numSimulations = 1
    for iterNum in range(0, numSimulations):
        for row in range(0, 48, 6):  #len(myMatrix), 6):          # for each group
            myGroup = {}
            myGroup[myMatrix[row]['Team 1']] = (0, 0, 0, 0)
            myGroup[myMatrix[row]['Team 2']] = (0, 0, 0, 0)
            myGroup[myMatrix[row + 1]['Team 2']] = (0, 0, 0, 0)
            myGroup[myMatrix[row + 2]['Team 2']] = (0, 0, 0, 0)
            for gameNum in range(0, 6): # for each match
                t1 = myMatrix[row + gameNum]['Team 1']
                t2 = myMatrix[row + gameNum]['Team 2']
                t1_rand = random.random()
                t2_rand = random.random()
                t1_goals = 0
                t2_goals = 0
                t1_found = False
                t2_found = False

                for goalNum in range(0, 6):
                    t1_goals = goalNum
                    goalsProb = myMatrix[row + gameNum]['P(T1_' + str(goalNum) + 'G)']
                    if t1_rand < goalsProb:
                        t1_found = True
                        break
                    else:
                        t1_rand -= goalsProb
                for goalNum in range(0, 6):
                    t2_goals = goalNum
                    goalsProb = myMatrix[row + gameNum]['P(T2_' + str(goalNum) + 'G)']
                    if t2_rand < goalsProb:
                        t2_found = True
                        break
                    else:
                        t2_rand -= goalsProb
                if not t1_found:
                    t1_goals = 6
                if not t2_found:
                    t2_goals = 6

                #assign points to each team
                t1_points = 0
                t2_points = 0
                if t1_goals == t2_goals:
                    t1_points = 1
                    t2_points = 1
                elif t1_goals > t2_goals:
                    t1_points = 3
                else:
                    t2_points = 3

                #update data
                t1_gf, t1_ga, t1_gd, t1_cur_points = myGroup[t1]
                t2_gf, t2_ga, t2_gd, t2_cur_points = myGroup[t2]
                t1_gf += t1_goals
                t1_ga -= t2_goals
                t1_gd += (t1_goals - t2_goals)
                t1_cur_points += t1_points
                t2_gf += t2_goals
                t2_ga -= t1_goals
                t2_gd += (t2_goals - t1_goals)
                t2_cur_points += t2_points
                myGroup[t1] = (t1_gf, t1_ga, t1_gd, t1_cur_points)
                myGroup[t2] = (t2_gf, t2_ga, t2_gd, t2_cur_points)
            groupRanks = rankTeams(myGroup)




            #
            # teamDict = {}
            # for gameNum in range(0, 6):
            #
            #
            #     print(myMatrix[row + gameNum])
            #
    #print(myGroup)

def print_all(team_elo):
    world_cup_teams = get_world_cup_teams(team_elo)
    workbook = xlsxwriter.Workbook('Poisson_predictions.xlsx')
    BOLD = workbook.add_format({'bold': True})

    cleaned_elo = print_scores(workbook, world_cup_teams)

    worksheet = workbook.add_worksheet('Match Predictions')
    print_match_prediction_labels(worksheet, BOLD)
    resultsMatrix = print_match_predictions(worksheet, world_cup_teams)

    simulate_matrix = create_sim_matrix(resultsMatrix)
    game_sims = simulate_games(simulate_matrix)

    workbook.close()

def choose_eta_weight(tourney):
    if "World Cup Qualification" in tourney:
        k = 0.0005
    elif "Copa America" in tourney or "Cup of Nations" in tourney or "Asian Cup" in tourney or "Euro Cup" in tourney or "Gold Cup" in tourney:
        k = 0.0005
    elif "World Cup" in tourney or "World Championship" in tourney:
        k = 0.001
    else:
        k = 0.0001
    return k

def get_continent_score(continent):
    switcher = {
        'Oceania' : 0.8, #759: sum of FIFA rankings of top 5 teams
        'Asia' : 1.2, #264
        'Africa' : 1.3, #168
        'North' : 1.3, #171
        'Europe' : 1.8, #21
        'South' : 2.2 #43
    }
    return switcher.get(continent, ValueError("This should never happen"))

def calc_elo(numIterations):
    #read in the results of previous games
    sheet = pd.read_csv('src/scoresParsed.csv')
    sheet.dropna()

    #initialization parameters
    team_elo = {}
    base_score = 1.35
    eta = 0.001

    for i, row in sheet.iterrows():
        t1 = row['Home team']
        t2 = row['Away team']
        competition = row['Event Name']
        continent = competition.split(' ', 1)[0]
        if continent == 'World':
            continue

        if t1 not in team_elo:
            team_elo[t1] = (continent, base_score, base_score)
        if t2 not in team_elo:
            team_elo[t2] = (continent, base_score, base_score)

    for x in range(0,numIterations):
        print("Currently on attempt ", x)
        for i, row in sheet.iterrows():
            t1 = row['Home team']
            t2 = row['Away team']

            eta = choose_eta_weight(row['Event Name'])

            # some countries (Basque Country or Catalonia's games are ignored)
            if (t1 not in team_elo) or (t2 not in team_elo):
                continue

            t1_cont, t1_off, t1_def = team_elo[t1]
            t2_cont, t2_off, t2_def = team_elo[t2]
            cont_power_ratio = get_continent_score(t1_cont)/get_continent_score(t2_cont)

            actual_t1_goals = max(row['Hometeam Halftime'], row['Hometeam Fulltime'], row['Hometeam Overtime'], row['Hometeam Extratime'])
            actual_t2_goals = max(row['Awayteam Halftime'], row['Awayteam Fulltime'], row['Awayteam Overtime'], row['Awayteam extratime'])
            expected_t1_goals = cont_power_ratio * base_score * t1_off/t2_def
            expected_t2_goals = (1/cont_power_ratio) * base_score * t2_off/t1_def

            if(math.isnan(actual_t1_goals) or math.isnan(actual_t2_goals)):
                continue

            t1_error = actual_t1_goals - expected_t1_goals
            t2_error = actual_t2_goals - expected_t2_goals

            t1_new_off = min(max((t1_off) + eta*t1_error, 0.25), 4)
            t1_new_def = min(max((t1_def) - eta*t2_error, 0.25), 4)
            t2_new_off = min(max((t2_off) + eta*t2_error, 0.25), 4)
            t2_new_def = min(max((t2_def) - eta*t1_error, 0.25), 4)

            team_elo[t1] = (t1_cont, t1_new_off, t1_new_def)
            team_elo[t2] = (t2_cont, t2_new_off, t2_new_def)

    new_team_elo = {}
    for team in team_elo:
        continent, off_score, def_score = team_elo[team]
        power = get_continent_score(continent)
        new_team_elo[team] = (continent, power*off_score, power*def_score)
    return new_team_elo
    #return team_elo

if __name__ == '__main__':
    team_elo = calc_elo(1)
    print_all(team_elo)
