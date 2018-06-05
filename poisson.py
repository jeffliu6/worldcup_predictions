import operator
import math
import pandas as pd
import xlsxwriter



def print_predictions(team_elo):
    workbook = xlsxwriter.Workbook('Poisson_predictions.xlsx')
    BOLD = workbook.add_format({'bold': True})
    worksheet = workbook.add_worksheet('ELO Scores')
    row, col = 1, 0

    worldcup_elo = {}
    sheet = pd.read_csv('path/participatingteams.csv')
    for i, sheet_row in sheet.iterrows():
        team = sheet_row['Teams']
        worldcup_elo[team] = team_elo[team]

    worksheet.write(0,0, 'Team', BOLD)
    worksheet.write(0,1, 'Off Score', BOLD)
    worksheet.write(0,2, 'Def Score', BOLD)
    for team in worldcup_elo:
        worksheet.write(row, col, team)
        worksheet.write(row, col+1, worldcup_elo[team][0])
        worksheet.write(row, col+2, worldcup_elo[team][1])
        row+=1

    worksheet = workbook.add_worksheet('Predictions')
    row, col = 1, 0
    worksheet.write(0,0, 'Team 1', BOLD)
    worksheet.write(0,1, 'Team 2', BOLD)
    worksheet.write(0,2, 'xG1', BOLD)
    worksheet.write(0,3, 'xG2', BOLD)
    # worksheet.write(0,8, 'P(1)', BOLD)
    # worksheet.write(0,9, 'P(2)', BOLD)
    for t1 in worldcup_elo:
        for t2 in worldcup_elo:
            if t1 == t2:
                continue
            worksheet.write(row, col, t1)
            worksheet.write(row, col + 1, t2)
            t1_off, t1_def = worldcup_elo[t1]
            t2_off, t2_def = worldcup_elo[t2]
            worksheet.write(row, col + 2, 1.35*t1_off/t2_def)
            worksheet.write(row, col + 3, 1.35*t2_off/t1_def)
            row+=1

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
    print_predictions(team_elo)
