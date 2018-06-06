import operator
import math
import pandas as pd
import xlsxwriter
import numpy as np

def print_scores(workbook, team_elo):
    BOLD = workbook.add_format({'bold': True})
    worksheet = workbook.add_worksheet('ELO Scores')
    row, col = 1, 0

    worldcup_elo = {}
    sheet = pd.read_csv('path/participatingteams.csv')
    for i, sheet_row in sheet.iterrows():
        team = sheet_row['Teams']
        group = sheet_row['Group']
        worldcup_elo[team] = (team_elo[team][0], team_elo[team][1], group[0], int(group[1]))

    worksheet.write(0,0, 'Team', BOLD)
    worksheet.write(0,1, 'Off Score', BOLD)
    worksheet.write(0,2, 'Def Score', BOLD)
    for team in worldcup_elo:
        worksheet.write(row, col, team)
        worksheet.write(row, col+1, worldcup_elo[team][0])
        worksheet.write(row, col+2, worldcup_elo[team][1])
        row+=1
    return worldcup_elo

def print_group_predictions(workbook, worldcup_elo):
    BOLD = workbook.add_format({'bold': True})
    worksheet = workbook.add_worksheet('Group Stage Predictions')
    row, col = 1, 0
    worksheet.write(0,0, 'Group', BOLD)
    worksheet.write(0,1, 'Team 1', BOLD)
    worksheet.write(0,2, 'Team 2', BOLD)
    worksheet.write(0,3, 'xG1', BOLD)
    worksheet.write(0,4, 'xG2', BOLD)

    worksheet.write(0,5, 'P(T1_0G)', BOLD)
    worksheet.write(0,6, 'P(T1_1G)', BOLD)
    worksheet.write(0,7, 'P(T1_2G)', BOLD)
    worksheet.write(0,8, 'P(T1_3G)', BOLD)
    worksheet.write(0,9, 'P(T1_4G)', BOLD)
    worksheet.write(0,10, 'P(T1_5G)', BOLD)
    worksheet.write(0,11, 'P(T1_6G+)', BOLD)

    worksheet.write(0,12, 'P(T2_0G)', BOLD)
    worksheet.write(0,13, 'P(T2_1G)', BOLD)
    worksheet.write(0,14, 'P(T2_2G)', BOLD)
    worksheet.write(0,15, 'P(T2_3G)', BOLD)
    worksheet.write(0,16, 'P(T2_4G)', BOLD)
    worksheet.write(0,17, 'P(T2_5G)', BOLD)
    worksheet.write(0,18, 'P(T2_6G+)', BOLD)

    for t1 in worldcup_elo:
        for t2 in worldcup_elo:
            t1_off, t1_def, t1_group, t1_pot = worldcup_elo[t1]
            t2_off, t2_def, t2_group, t2_pot = worldcup_elo[t2]
            if t1 == t2 or t1_group != t2_group or t1_pot > t2_pot:
                continue
            worksheet.write(row, col, t1_group)
            worksheet.write(row, col + 1, t1)
            worksheet.write(row, col + 2, t2)
            t1_xG = 1.35*t1_off/t2_def
            t2_xG = 1.35*t2_off/t1_def
            worksheet.write(row, col + 3, t1_xG)
            worksheet.write(row, col + 4, t2_xG)

            p_sum_t1 = 0
            p_sum_t2 = 0
            for x in range(0, 6):
                p_t1_xGoals = (t1_xG**x) * (np.exp(1)**(-1*t1_xG)) / math.factorial(x)
                p_t2_xGoals = (t2_xG**x) * (np.exp(1)**(-1*t2_xG)) / math.factorial(x)
                worksheet.write(row, col + 5 + x, p_t1_xGoals)
                worksheet.write(row, col + 12 + x, p_t2_xGoals)
                p_sum_t1+=p_t1_xGoals
                p_sum_t2+=p_t2_xGoals

            worksheet.write(row, col + 11, 1 - p_sum_t1)
            worksheet.write(row, col + 18, 1 - p_sum_t2)

            row+=1

def print_all(team_elo):
    workbook = xlsxwriter.Workbook('Poisson_predictions.xlsx')
    cleaned_elo = print_scores(workbook, team_elo)
    print_group_predictions(workbook, cleaned_elo)
    workbook.close()

def calc_elo():
    #read in the results of previous games
    sheet = pd.read_csv('path/scoresParsed.csv')
    sheet.dropna()

    #initialization parameters
    team_elo = {}
    base_score = 1.35
    eta = 0.001

    for x in range(0,100):
        print("Currently on attempt ", x)
        for i, row in sheet.iterrows():
            t1 = row['Home team']
            t2 = row['Away team']
            if t1 not in team_elo:
                team_elo[t1] = (base_score, base_score)
            if t2 not in team_elo:
                team_elo[t2] = (base_score, base_score)

            t1_off, t1_def = team_elo[t1]
            t2_off, t2_def = team_elo[t2]

            actual_t1_goals = max(row['Hometeam Halftime'], row['Hometeam Fulltime'], row['Hometeam Overtime'], row['Hometeam Extratime'])
            actual_t2_goals = max(row['Awayteam Halftime'], row['Awayteam Fulltime'], row['Awayteam Overtime'], row['Awayteam extratime'])
            expected_t1_goals = base_score * t1_off/t2_def
            expected_t2_goals = base_score * t2_off/t1_def

            if(math.isnan(actual_t1_goals) or math.isnan(actual_t2_goals)):
                continue

            t1_error = actual_t1_goals - expected_t1_goals
            t2_error = actual_t2_goals - expected_t2_goals

            t1_new_off = min(max((t1_off) + eta*t1_error, 0.25), 4)
            t1_new_def = min(max((t1_def) - eta*t2_error, 0.25), 4)
            t2_new_off = min(max((t2_off) + eta*t2_error, 0.25), 4)
            t2_new_def = min(max((t2_def) - eta*t1_error, 0.25), 4)

            team_elo[t1] = (t1_new_off, t1_new_def)
            team_elo[t2] = (t2_new_off, t2_new_def)

    # for team in team_elo:
    #     print(team, team_elo[team][0], team_elo[team][1])
    return team_elo

if __name__ == '__main__':
    team_elo = calc_elo()
    print_all(team_elo)
