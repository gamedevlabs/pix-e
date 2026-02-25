import type { Paper, Finding } from '~/utils/priorFindings'

export const papers: Paper[] = [
  {
    id: 'lin19',
    title: 'An Empirical Study of Game Reviews on the Steam Platform',
    year: 2019,
    citation: 'Lin et al.',
  },
  {
    id: 'ma24',
    title: 'Cultural Perspectives on User Review Disparities: A Comparative Study of East Asian and Western Players on Steam',
    year: 2024,
    citation: 'Ma & Jenkel',
  },
  {
    id: 'zagal13',
    title: 'Cultural Differences in Game Appreciation: A Study of Player Game Reviews',
    year: 2013,
    citation: 'Zagal and Tomuro',
  },
  {
    id: 'ngai05',
    title: 'Cultural Influences on Video Games: Players\' Preferences in Narrative and Game-Play.',
    year: 2015,
    citation: 'Ngai',
  },
  {
    id: 'guzsvinecz23length',
    title: 'Length and sentiment analysis of reviews about top-level video game genres on the steam platform',
    year: 2023,
    citation: 'Guzsvinecz and Szucs',
  },
  {
    id: 'guzsvinecz23correlation',
    title: 'The correlation between positive reviews, playtime, design and game mechanics in souls-like role-playing video games',
    year: 2023,
    citation: 'Guzsvinecz',
  },
  {
    id: 'petrosino22',
    title: 'The Panorama of Steam Multiplayer Games (2018-2020): A Player Reviews Analysis',
    year: 2022,
    citation: 'Petrosino et al.',
  },
  {
    id: 'lin18',
    title: 'An Empirical Study of Early Access Games on the Steam Platform',
    year: 2018,
    citation: 'Lin et al.',
  },
  {
    id: 'bais17',
    title: 'Sentiment Classification on Steam Reviews',
    year: 2017,
    citation: 'Bais et al.',
  },
]




export const findings: Finding[] = [
  {
    id: 'lin19_1',
    paperId: 'lin19',
    quote: '96% of the games receive a median of less than 10 reviews per day.',
    tags: ['volume'],
  },
  {
    id: 'lin19_2',
    paperId: 'lin19',
    quote: 'Most games receive reviews with a median length of 205 characters, or 30 words.',
    tags: ['length'],
  },
  {
    id: 'lin19_3',
    paperId: 'lin19',
    quote: 'Negative reviews are slightly longer than positive reviews, but the difference is negligible.',
    tags: ['polarity', 'length'],
  },
  {
    id: 'lin19_4',
    paperId: 'lin19',
    quote: 'Early access reviews are slightly longer than non-early access reviews.',
    tags: ['early_access', 'length'],
  },
  {
    id: 'lin19_5',
    paperId: 'lin19',
    quote: 'Players write longer reviews for games for which they paid.',
    tags: ['cost', 'length'],
  },
  {
    id: 'lin19_6',
    paperId: 'lin19',
    quote: 'Reviews for indie games are longer than reviews for non-indie games.',
    tags: ['indie', 'length'],
  },
  {
    id: 'lin19_7',
    paperId: 'lin19',
    quote: 'Games receive a median of 36% non-English reviews.',
    tags: ['language'],
  },
  {
    id: 'lin19_8',
    paperId: 'lin19',
    quote: 'Reviews have a median readability level of grade 8.',
    tags: ['readability'],
  },
  {
    id: 'lin19_9',
    paperId: 'lin19',
    quote: 'The number of players has the strongest relation with the number of reviews.',
    tags: ['popularity'],
  },
  {
    id: 'lin19_10',
    paperId: 'lin19',
    quote:
      'A sale event has a stronger relation with an increase in the number of received reviews than releasing an update.',
    tags: ['popularity', 'sales', 'update'],
  },
  {
    id: 'lin19_11',
    paperId: 'lin19',
    quote: '42% of the reviews provide valuable information to developers.',
    tags: ['helpfulness'],
  },
  {
    id: 'lin19_12',
    paperId: 'lin19',
    quote: 'Players complain more about game design than bugs.',
    tags: ['game_design', 'bugs'],
  },
  {
    id: 'lin19_13',
    paperId: 'lin19',
    quote:
      'Negative reviews contain more valuable information about the negative aspects of a game for developers.',
    tags: ['helpfulness', 'polarity'],
  },
  {
  id: 'lin19_14',
  paperId: 'lin19',
  quote:
    'Positive reviews also provide useful information.',
  tags: ['helpfulness', 'polarity'],
},
  {
  id: 'lin19_15',
  paperId: 'lin19',
  quote:
    'Early access games receive more bug reports and suggestions.',
  tags: ['early_access', 'bugs','helpfulness'],
},
  {
  id: 'lin19_16',
  paperId: 'lin19',
  quote:
    'Indie games receive more suggestions than non-indie games.',
  tags: ['indie','helpfulness'],
},
  {
  id: 'lin19_17',
  paperId: 'lin19',
  quote:
    'Gamers play a game for a median of 13.5 hours before posting a review.',
  tags: ['playtime'],
},
  {
  id: 'lin19_18',
  paperId: 'lin19',
  quote:
    'Negative reviews are posted after significantly less playing hours than positive reviews.',
  tags: ['playtime','polarity'],
},
  {
  id: 'lin19_19',
  paperId: 'lin19',
  quote:
    'A peak in the number of reviews of free-to-play games is observed after approximately one hour of playing.',
  tags: ['cost','playtime'],
},
  {
  id: 'lin19_20',
  paperId: 'lin19',
  quote:
    'Indie game developers have a shorter time to satisfy players in their games than non-indie game developers.',
  tags: ['indie','playtime'],
},
  {
  id: 'lin19_21',
  paperId: 'lin19',
  quote:
    'Players of games in the early access stage spend more time playing a game before posting a review.',
  tags: ['early_access','playtime'],
},
  {
  id: 'lin19_22',
  paperId: 'lin19',
  quote:
    'Players of casual games spend the least time playing a game before posting a review.',
  tags: ['genre:casual','playtime'],
},
  {
  id: 'ma24_1',
  paperId: 'ma24',
  quote:
    'Our analysis reveals that East Asian players tend to provide lower user ratings compared to their Western counterparts.',
  tags: ['cultural','polarity'],
},
  {
  id: 'ma24_2',
  paperId: 'ma24',
  quote:
    'The results (Table 2) confirm that East Asian languages—Simplified Chinese, Traditional Chinese, Korean, and Japanese—have significantly lower user ratings. For instance, Simplified Chinese reviews exhibit an average positive rate of 76.9%, well below the global average of 84.7% (p < 0.001).',
  tags: ['cultural','polarity'],
},
  {
  id: 'ma24_3',
  paperId: 'ma24',
  quote:
    'A smaller ScoreGap signifies a closer alignment between the two review ratings. Our findings suggest that games with higher positive review ratings tend to have a smaller ScoreGap, indicating that when games are well-received, the reviews in both Chinese and English are more closely aligned. In contrast, games with lower user ratings exhibit a larger ScoreGap, especially within the range of 30 to 60.',
  tags: ['cultural','polarity'],
},
  {
  id: 'ma24_4',
  paperId: 'ma24',
  quote:
    'East Asian players demonstrate heightened sensitivity to game pricing, particularly for high-cost titles.',
  tags: ['cultural','cost'],
},
  {
  id: 'ma24_5',
  paperId: 'ma24',
  quote:
    'Our analysis shows that games that have undergone Early Access or are currently in that phase tend to receive higher user ratings globally, a trend reflected in English reviews as well. In contrast, Chinese reviews indicate a slightly lower user rating for Early Access games.',
  tags: ['cultural','early_access'],
},
  {
  id: 'zagal13_1',
  paperId: 'zagal13',
  quote:
    'We found that, while preferences in the both cultures are generally similar, they are sensitive to different aspects: for example, American players emphasize the replay value of a game, whereas Japanese players are less tolerant of bugs and emphasize overall polish.',
  tags: ['cultural','bugs'],
},
  {
  id: 'zagal13_2',
  paperId: 'zagal13',
  quote:
    'while Japanese players rate yoge (Western) games favorably, they seem to have lower expectations of overall quality.',
  tags: ['cultural','bugs'],
},
  {
  id: 'zagal13_3',
  paperId: 'zagal13',
  quote:
    'The strongest correlations occur within cultures (A for the US, and B for Japan), indicating at least a broad level of agreement between critics and users in the same culture.',
  tags: ['cultural','polarity'],
},
  {
  id: 'zagal13_4',
  paperId: 'zagal13',
  quote:
    'The correlation between the players (D) is distinctly lower than the rest suggesting there may be differences in appreciation of the same games between US and Japanese players.',
  tags: ['cultural','polarity'],
},
  {
  id: 'zagal13_5',
  paperId: 'zagal13',
  quote:
    'From the mean values, Japanese users (Game World) are the harshest critics (66.43) while Gamespot Users [American] are the most lenient (77.90).',
  tags: ['cultural','polarity'],
},
  {
  id: 'zagal13_6',
  paperId: 'zagal13',
  quote:
    'We obtained several findings, including that users in neither culture have bias for or against particular platforms [PS3, X360, Wii, DS, PSP] and that preferences of the users in the two cultures are generally similar.',
  tags: ['cultural','platforms'],
},
  {
  id: 'ngai05_1',
  paperId: 'ngai05',
  quote:
    'As this case study indicates, Japanese developers design games with a higher level of narrative content then their US counterparts; enjoyment through game-play is provided by strategic elements rather than physical actions. US developers are more into designing gameplay with physical actions; enjoyment is provided through constant interactivity, and exploration of possibilities.',
  tags: ['cultural','game_design'],
},
  {
  id: 'ngai05_2',
  paperId: 'ngai05',
  quote:
    'Although both groups remain to have a high level of interest in playing video games, Japanese respondents view video games as pure entertainment, something to kill their time with, while American respondents would be more incline to dedicate time for playing video games as a hobby.',
  tags: ['cultural'],
},
  {
  id: 'ngai05_3',
  paperId: 'ngai05',
  quote:
    'Although no major differences were found, given the small sample population, it could be seen that there was a greater sense of character attachment from Japanese respondents, while American respondents did not like to be forced away from their actions by “long” narrative elements.',
  tags: ['cultural','game_design'],
},
  {
  id: 'ngai05_4',
  paperId: 'ngai05',
  quote:
    'There are also differences between Japan and the US in terms of control. Interestingly enough, American respondents perceive they have control over the outcome or game progress in role-playing games, as compared to Japanese respondents who perceive they have control in action adventure games. This could be explained by the different types of role-playing game. In the US, role-playing games are often free-structured, as oppose to those strictly defined ones in Japan, similar to the two games described in the case study. Since less defined structure would increase the degree of freedom, American respondents could perceive themselves having the control over game’s progression.',
  tags: ['cultural','game_design'],
},
  {
  id: 'ngai05_5',
  paperId: 'ngai05',
  quote:
    'For story development, American respondents (86.7%) show a higher level of curiosity than Japanese respondents (78.3%). There are similar results for curiosity about upcoming tasks with 73.8% of Japanese respondents and 82.2% of American respondents either stating they “agree” or “disagree” to the statement.',
  tags: ['cultural','game_design'],
},
  {
  id: 'ngai05_6',
  paperId: 'ngai05',
  quote:
    'Japanese respondents state that they become emotional over story development (18%), unable to progress or finish a game (18%), and game completion (14%). For the American respondents, story development is also most frequently mentioned (34.2%), following by death of a character (23.7%), game completion (10.5%) and competition / cooperation with others (10.5%).',
  tags: ['cultural','game_design'],
},
  {
  id: 'ngai05_7',
  paperId: 'ngai05',
  quote:
    'Responses are once again grouped into categories, and indicate Japanese respondents think it is boring when the game becomes too difficult (19.2%) or the story is too trivial and simple (19.2%). Most of the American respondents, however, think it is boring when the tasks are being repetitive and tedious (33.3%), or story is too trivial and simple (15.9%). Answers among the two groups are not statistical different (Fisher’s exact test: p-value = 0.1296).',
  tags: ['cultural','game_design'],
},
  {
  id: 'guzsvinecz23length_1',
  paperId: 'guzsvinecz23length',
  quote:
    'Word numbers significantly differ between TLGs as can be observed in Table 4. The longest positive and negative reviews are written for RPGs, while the shortest positive and negative reviews are written for racing games. However, the number of words is significantly larger in case of negative reviews in every TLG. Overall, the median word count for positive reviews is 19, while it is 40 for negative ones.',
  tags: ['genres','length','polarity'],
},
  {
  id: 'guzsvinecz23length_2',
  paperId: 'guzsvinecz23length',
  quote:
    'Positive reviews are written much later (Mdnp ≈6.76 hours of playtime) than negative ones (Mdnn ≈2.06 hours of playtime). In the case of negative reviews, tabletop games are played for the most hours before reviewing, while in the case of positive reviews, simulation games are played for the most hours. Experimental games were played for the least amount of time before reviewing in the case of both review types.',
  tags: ['genres','playtime','polarity'],
},
  {
  id: 'guzsvinecz23length_3',
  paperId: 'guzsvinecz23length',
  quote:
    'There is no correlation between word numbers and time at review. This is the case in all TLGs. Whether the review’s type is positive or negative, it only weakly affects the strength of the correlation coefficient. However, an analysis should be conducted in smaller genres or sub-genres.',
  tags: ['genres','playtime','length'],
},
  {
  id: 'guzsvinecz23length_4',
  paperId: 'guzsvinecz23length',
  quote:
    'Even though negative reviews contain more negative sentiments, all reviews start on a somewhat positive emotional valence. As people write reviews, they tend to experience negative emotions, decreasing the emotional valence through narrative time. In most TLGs, the decrease of emotional valence through narrative time is stronger in negative reviews. There are some TLGs in which the valence increases a little in the end.',
  tags: ['genres','polarity','sentiment'],
},
  {
  id: 'guzsvinecz23length_5',
  paperId: 'guzsvinecz23length',
  quote:
    'The average number of emotions per review is significantly different among TLGs. However, some similarities in the average number of emotions between TLGs could be found in positive reviews, while they increase in negative ones. By analyzing the emotions in text, racing and sports games proved to be the most similar in case of negative reviews.',
  tags: ['genres','polarity','sentiment'],
},
  {
  id: 'guzsvinecz23correlation_1',
  paperId: 'guzsvinecz23correlation',
  quote:
    'According to the results, a slight-to-moderate correlation exists between positive reviews and the users’ playtimes: more playtimes mean a larger chance of having positive reviews.',
  tags: ['polarity','playtime','genre:Souls-like'],
},
  {
  id: 'guzsvinecz23correlation_2',
  paperId: 'guzsvinecz23correlation',
  quote:
    'Out of the investigated 11 factors, significant differences exist among all of them: drawn graphics (96.48%) and 2D style (95.61%) are the two most liked factors, while pixel graphics (87.11%) and a futuristic setting (86.74%) are the two least liked ones.',
  tags: ['game_design','genre:Souls-like'],
},
  {
  id: 'guzsvinecz23correlation_3',
  paperId: 'guzsvinecz23correlation',
  quote:
    'Every factor has a significant influence on the percentage of positive reviews. According to the results presented in this article, users liked the following group the most: game, with a medieval setting, 2D graphics, a drawn graphical style, an interconnected world, no difficulty settings, no multiplayer features, weapon upgrades, no equipment durability, a map, additional penalties upon character death and a not classic level-up system.',
  tags: ['game_design', 'polarity', 'genre:Souls-like'],
},
  {
  id: 'guzsvinecz23correlation_4',
  paperId: 'guzsvinecz23correlation',
  quote:
    'Almost every factor can significantly affect all eight basic emotions (anger, anticipation, disgust, fear, joy, sadness, surprise, trust).',
  tags: ['game_design', 'sentiment', 'genre:Souls-like'],
},
  {
  id: 'guzsvinecz23correlation_5',
  paperId: 'guzsvinecz23correlation',
  quote:
    'As can be seen in Fig. 5, trust, anticipation, and joy were the three most largely felt emotions when writing the reviews. Their percentages were 16.68%, 15.32%, and 14.15%, respectively.',
  tags: ['sentiment', 'genre:Souls-like'],
},
  {
  id: 'guzsvinecz23correlation_6',
  paperId: 'guzsvinecz23correlation',
  quote:
    'Darksiders III was the one that made most people angry (14.88%) and was most feared (15.67%). It is not surprising as its prequels were not “Souls-like”: Darksiders I was a simple“hack’n’slash” game, while Darksiders II was an open-world roleplaying game.',
  tags: ['sentiment', 'genre:Souls-like'],
},
  {
  id: 'petrosino22_1',
  paperId: 'petrosino22',
  quote:
    'Our findings show an increase of people playing and reviewing games during the first year of the pandemic in which stay-at-home orders and other restrictions were implemented.',
  tags: ['covid','playtime'],
},
  {
  id: 'petrosino22_2',
  paperId: 'petrosino22',
  quote:
    'Contrary to what we expected, we did not find a strong negative sentiment among reviews. In fact, reviews written in 2020 during the pandemic were shorter and less helpful for the community, suggesting an influx of new/casual players and a general increase in activities.',
  tags: ['covid','sentiment', 'helpfulness'],
},
  {
  id: 'petrosino22_3',
  paperId: 'petrosino22',
  quote:
    'Furthermore, gamers played more casual games, which had a lower barrier of entry and could be enjoyed even with friends who may not have had any prior gaming experience.',
  tags: ['covid','genres'],
},
  {
  id: 'petrosino22_4',
  paperId: 'petrosino22',
  quote:
    'Here, the results showed that compared to the previous years, the sentiment in the reviews players wrote is simultaneously less positive and less negative. What was defined as a neutral sentiment in this paper has increased significantly compared to 2018 and 2019. This leads us to the conclusion that while gamers wrote more reviews, they were less likely to express a strong and clear opinion.',
  tags: ['covid','sentiment'],
},
  {
  id: 'lin18_1',
  paperId: 'lin18',
  quote:
    '15% of the games on Steam make use of the early access model and its popularity is growing. Of the 8,025 games that are available on Steam, 786 games are current EAGs, and 396 games are former EAGs. As a result, 1,182 (15%) games are or were making use of the early access model.',
  tags: ['early_access','volume'],
},
  {
  id: 'lin18_2',
  paperId: 'lin18',
  quote:
    '25% of the EAGs have more than 48 thousand owners, with almost 29 million owners for one of the studied EAGs.',
  tags: ['early_access','volume'],
},
  {
  id: 'lin18_3',
  paperId: 'lin18',
  quote:
    '34% of all EAGs have left the early access stage.',
  tags: ['early_access'],
},
  {
  id: 'lin18_4',
  paperId: 'lin18',
  quote:
    '88% of the EAGs are indie games, indicating that most EAGs are developed by individual developers or small studios.',
  tags: ['early_access', 'indie'],
},
  {
  id: 'lin18_5',
  paperId: 'lin18',
  quote:
    'Most former EAGs have spent less than a year in the early access stage.',
  tags: ['early_access'],
},
  {
  id: 'lin18_6',
  paperId: 'lin18',
  quote:
    '63% of the EAGs update more frequently in their early access stage.',
  tags: ['early_access', 'update'],
},
  {
  id: 'lin18_7',
  paperId: 'lin18',
  quote:
    '65% of the EAGs see an equal or lower activity of owners posting reviews in the early access stage.',
  tags: ['early_access', 'volume'],
},
  {
  id: 'lin18_8',
  paperId: 'lin18',
  quote:
    '81% of the EAGs observe an equal or higher activity on the discussion forums in the early access stage.',
  tags: ['early_access', 'volume'],
},
  {
  id: 'lin18_9',
  paperId: 'lin18',
  quote:
    '89% of the EAGs receive an equally or higher positive review rate during their early access stage.',
  tags: ['early_access', 'polarity'],
},
  {
  id: 'lin18_10',
  paperId: 'lin18',
  quote:
    'The positive review rate is not correlated with either the length of the early access stage or the update frequency in the early access stage',
  tags: ['early_access', 'polarity','length','update'],
},
  {
  id: 'lin18_11',
  paperId: 'lin18',
  quote:
    '145 (48.3%) of the remaining former EAGs have the same median price within and after leaving the early access stage, while 91 (30.3%) increase their price and 64 (21.3%) decrease their price.',
  tags: ['early_access', 'cost'],
},
  {
  id: 'bais17_1',
  paperId: 'bais17',
  quote:
    'Our baseline, as expected under-performed, with an average accuracy of 59 percent. The errors for this method sprouted when it couldn’t find the subtleties in the sentences. For many positive examples, there were reviews saturated with positive words and fewer negative words but it was not able to grasp the concluding sentiment, despite being much shorter than the rest of the review, is the true sentiment. As an example, “I thought the prequel was fantastic and great, but this is horrendous” starts off positively and ends negatively, but our method would see more positive words than negative words and label it positive.',
  tags: ['sentiment', 'sarcasm'],
},
  {
  id: 'bais17_2',
  paperId: 'bais17',
  quote:
    'From observing, SVM with TF-IDF and positional weighting outperformed the others because with additional features like hours played and proper weighting of indicative words, it is able to work through sarcastic reviews and determine the true sentiment.',
  tags: ['sentiment', 'sarcasm'],
},



]
