from collections import Counter
import matplotlib.pyplot as plt 

def pie_malformed(well_formed, malformed):
  labels = ['Well-formed', 'Malformed']
  values = [well_formed, malformed]

  #add colors
  colors = ['#F5891C','#b9b9b9']

  fig1, ax1 = plt.subplots(figsize=(6, 5))
  patches, texts, autotexts = ax1.pie(values, colors=colors, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.55)
  for text in texts:
      text.set_color('#414141')
  for autotext in autotexts:
      autotext.set_color('#414141')

  #draw circle
  centre_circle = plt.Circle((0,0),0.75,fc='white')
  fig = plt.gcf()
  fig.gca().add_artist(centre_circle)

  # Equal aspect ratio ensures that pie is drawn as a circle
  ax1.axis('equal')  
  plt.tight_layout()

  plt.savefig("plots/pie_malformed" + ".png",
                 format="png",
                 dpi=300,
                 bbox_inches="tight",
                 pad_inches=0.5)

def bar_citation_types(matched_rule_type):
  rule_type_counts = Counter(matched_rule_type)
  rule_type_counts = dict(sorted(rule_type_counts.items(), key=lambda pair: pair[1]))
  plt.figure(figsize=(30,40))
  plt.barh(list(rule_type_counts.keys()), rule_type_counts.values(), color='#F5891C')

  plt.xticks(fontsize = 20, color='#414141')
  plt.yticks(fontsize = 20, color='#414141')
  plt.xlabel("Count", fontsize = 25, labelpad=25, color='#414141')
  plt.ylabel("Matched Rule", fontsize = 25, labelpad=20, color='#414141')
  plt.tick_params(axis='both', pad=10)

  plt.gca().spines['top'].set_visible(False)
  plt.gca().spines['right'].set_visible(False)
  plt.grid(axis='x', linewidth=0.6, color='#414141', zorder=0)

  plt.tight_layout() 
  plt.savefig("plots/bar_types"+".png")

def bar_citation_year(years):
  year_counts = Counter(years)
  year_counts = dict(sorted(year_counts.items(), key=lambda pair: pair[1]))
  plt.figure(figsize=(30,40))
  plt.barh(list(year_counts.keys()), year_counts.values(), color='#F5891C')

  plt.xticks(fontsize = 20, color='#414141')
  plt.yticks(fontsize = 20, color='#414141')
  plt.xlabel("Count", fontsize = 25, labelpad=25, color='#414141')
  plt.ylabel("Year", fontsize = 25, labelpad=20, color='#414141')
  plt.tick_params(axis='both', pad=10)

  plt.gca().spines['top'].set_visible(False)
  plt.gca().spines['right'].set_visible(False)
  plt.grid(axis='x', linewidth=0.6, color='#414141', zorder=0)

  plt.tight_layout() 
  plt.savefig("plots/bar_years"+".png")

def bar_malformed_type(malformed_types):
  malformed_type_counts = Counter(malformed_types)
  malformed_type_counts = dict(sorted(malformed_type_counts.items(), key=lambda pair: pair[1]))
  plt.figure(figsize=(30,20))
  plt.barh(list(malformed_type_counts.keys()), malformed_type_counts.values(), color='#F5891C')

  plt.xticks(fontsize = 20, color='#414141')
  plt.yticks(fontsize = 20, color='#414141')
  plt.xlabel("Count", fontsize = 25, labelpad=25, color='#414141')
  plt.ylabel("Malformed Rule Type", fontsize = 25, labelpad=20, color='#414141')
  plt.tick_params(axis='both', pad=10)

  plt.gca().spines['top'].set_visible(False)
  plt.gca().spines['right'].set_visible(False)
  plt.grid(axis='x', linewidth=0.6, color='#414141', zorder=0)

  plt.tight_layout() 
  plt.savefig("plots/bar_malformed_type"+".png")

def citations_hist(citation_count):
  plt.figure(figsize=(30,20))
  plt.hist(citation_count, density=True, color='#F5891C')  # density=False would make counts
  
  plt.xticks(fontsize = 20, color='#414141')
  plt.yticks(fontsize = 20, color='#414141')
  plt.xlabel("Citations", fontsize = 25, labelpad=25, color='#414141')
  plt.ylabel("Probability", fontsize = 25, labelpad=20, color='#414141')
  plt.tick_params(axis='both', pad=10)

  plt.gca().spines['top'].set_visible(False)
  plt.gca().spines['right'].set_visible(False)
  plt.grid(axis='y', linewidth=0.6, color='#414141', zorder=0)
  
  plt.savefig("plots/citation_hist"+".png")