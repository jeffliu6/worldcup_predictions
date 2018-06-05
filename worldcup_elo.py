import operator
import math
import pandas as pd
import xlsxwriter

def print_scores(sorted_elo, workbook):
    BOLD = workbook.add_format({'bold': True})
    worksheet = workbook.add_worksheet('ELO Scores')
    worksheet.write(0,0, 'Team', BOLD)
    worksheet.write(0,1, 'ELO Score', BOLD)
    row, col = 1, 0
    for team in sorted_elo:
        worksheet.write(row, 0, team[0])
        worksheet.write(row, 1, team[1])
        row+=1

def print_predictions(team_elo, workbook):
    BOLD = workbook.add_format({'bold': True})
    worksheet = workbook.add_worksheet('Predictions')
    row, col = 1, 0
    worksheet.write(0,0, 'Team 1', BOLD)
    worksheet.write(0,1, 'Team 2', BOLD)
    worksheet.write(0,2, 'ELO1', BOLD)
    worksheet.write(0,3, 'ELO2', BOLD)
    worksheet.write(0,4, 'ELO Difference', BOLD)
    worksheet.write(0,5, 'P1', BOLD)
    worksheet.write(0,6, 'P2', BOLD)
    worksheet.write(0,7, 'xG1', BOLD)
    worksheet.write(0,8, 'xG2', BOLD)
    worksheet.write(0,9, 'Winner', BOLD)
    for t1 in team_elo:
        for t2 in team_elo:
            if t1 == t2:
                continue
            p1 = 1 / (1 + 10 ** ((team_elo[t2] - team_elo[t1]) / 400))
            p2 = 1 / (1 + 10 ** ((team_elo[t1] - team_elo[t2]) / 400))
            winner = t1 if p1 > p2 else t2
            worksheet.write(row, col, t1)
            worksheet.write(row, col + 1, t2)
            worksheet.write(row, col + 2, team_elo[t1])
            worksheet.write(row, col + 3, team_elo[t2])
            worksheet.write(row, col + 4, team_elo[t1]-team_elo[t2])
            worksheet.write(row, col + 5, p1)
            worksheet.write(row, col + 6, p2)
            temp1 = 1.05*(1.28**((team_elo[t1]-team_elo[t2])/100))
            temp2 = 1.05*(1.28**((team_elo[t2]-team_elo[t1])/100))
            worksheet.write(row, col + 7, temp1)
            worksheet.write(row, col + 8, temp2)
            worksheet.write(row, col + 9, winner)
            row+=1

def print_all(team_elo):
    workbook = xlsxwriter.Workbook('ELO_predictions.xlsx')
    sorted_elo = sorted(team_elo.items(), key=operator.itemgetter(1), reverse=True)
    print_scores(sorted_elo, workbook)
    print_predictions(team_elo, workbook)
    workbook.close()
    return sorted_elo

def choose_weight(inputs, tourney):
    if "World Cup Qualification" in tourney:
        k = inputs[2]
    elif "Copa America" in tourney or "Cup of Nations" in tourney or "Asian Cup" in tourney or "Euro Cup" in tourney or "Gold Cup" in tourney:
        k = inputs[3]
    elif "World Cup" in tourney or "World Championship" in tourney:
        k = inputs[4]
    else:
        k = inputs[0]
    return k

def calc_elo(inputs):
    # total_goals = 0
    # total_games = 0
    #read in the results of previous games
    sheet = pd.read_csv('path/scoresParsed.csv')
    sheet.dropna()

    #initialization parameters
    team_elo = {}
    columns = ['Team 1', 'Team 2', 'Team 1 Prob', 'Team 2 Prob', 'Winner Prediction', 'Actual Winner', 'Correct']
    current_year = int(sheet['Date'][0][8:12])
    base_elo = 1200
    carry = inputs[0] # the carry over from year to year
    k = 0 # k is the weight of the game

    total_correct = 0
    count = 0

    for i, row in sheet.iterrows():
        k = choose_weight(inputs, row['Event Name'])

        t1 = row['Home team']
        t2 = row['Away team']
        if t1 not in team_elo:
            team_elo[t1] = base_elo
        if t2 not in team_elo:
            team_elo[t2] = base_elo
        p1 = 1 / (1 + 10 ** ((team_elo[t2] - team_elo[t1]) / 400))
        p2 = 1 / (1 + 10 ** ((team_elo[t1] - team_elo[t2]) / 400))
        winner = t1 if p1 > p2 else t2

        # sometimes the score is broken, so we want the maximum goals scored by each team
        home_score = max(row['Hometeam Halftime'], row['Hometeam Fulltime'], row['Hometeam Overtime'], row['Hometeam Extratime'])
        away_score = max(row['Awayteam Halftime'], row['Awayteam Fulltime'], row['Awayteam Overtime'], row['Awayteam extratime'])

        # sometimes the score isn't reported
        if(math.isnan(home_score) or math.isnan(away_score)):
            continue
        # total_games+=1
        # total_goals+=(home_score + away_score)

        if home_score > away_score:
            actual = t1
        elif home_score == away_score:
            actual = 'Draw'
        else:
            actual = t2

        if actual == t1:
            team_elo[t1] += k * (1 - p1)
            team_elo[t2] += k * (0 - p2)
        elif actual == t2:
            team_elo[t2] += k * (1 - p2)
            team_elo[t1] += k * (0 - p1)
        elif actual == 'Draw':
            team_elo[t2] += k * (0.5 - p2)
            team_elo[t1] += k * (0.5 - p1)

        game_date = str(row['Date'])
        # how much of last year's ELO is kept
        if len(game_date)>3 and int(game_date[8:12]) > current_year:
            current_year = int(game_date[8:12])
            for team in team_elo:
                team_elo[team] = carry*team_elo[team] + (1-carry)*base_elo

        correct = int(winner == actual)
        if current_year == 2018:
            total_correct += correct
            count += 1

    accuracy = total_correct / count
    print('Accuracy: {}'.format(accuracy))
    #print('average goals', total_goals/total_games)
    return team_elo

if __name__ == '__main__':
    # k, friendly, qualification, continental tourney, world cup
    team_elo = calc_elo([0.9, 10, 20, 30, 40])
    sorted_elo = print_all(team_elo)
    #from scipy.optimize import minimize
    #res = minimize(main, [0.9, 10, 20, 30, 40], bounds=[(0, 1), (0, None), (0, None), (0, None), (0, None)], method='TNC', options=dict(maxiter=20))
    #print(res)
