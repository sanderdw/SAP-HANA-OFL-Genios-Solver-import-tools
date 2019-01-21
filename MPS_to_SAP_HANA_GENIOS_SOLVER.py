# Converts MPS problems to csv's for SAP HANA Genius Solver input tables
# Questions? Sander de Wildt: info@sanderdewildt.nl

# Docs:
# http://lpsolve.sourceforge.net/5.5/Python.htm
# http://lpsolve.sourceforge.net/5.0/mps-format.htm
# See also o10n-AFL-231118-1438-5834.pdf for documentation about the Genius Solver in SAP HANA

# create python37 env
# conda install -c rmg lpsolve55
# Not needed: conda install -c rmg lpsolve
from lpsolve55 import *
import csv
import configparser
import os 
# Configuration enviroment paths
config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'MPS_to_SAP_HANA_GENIOS_SOLVER_config.ini'))
source_directory = config.get('Paths', 'source_directory')
target_directory = config.get('Paths', 'target_directory')

# Configuration input MPS file
source_filename = 'pilot4.mps'

# Load MPS
lp = lpsolve('read_mps', source_directory + source_filename)
lpsolve('return_constants', 1)

# Write an LP formatted file for reference (Optional)
# lpsolve('write_lp', lp, target_directory + source_filename + '.lp')

# Get dimensions
nrrows_orig = lpsolve('get_Norig_rows', lp)
nrcolumns_orig = lpsolve('get_Norig_columns', lp)

# P6 - OBJECTIVEMONOMES
with open(target_directory + source_filename + '_IT_OBJECTIVE_MONOM' + '.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write header
    spamwriter.writerow(['VARIABLEID', 'COEFFICIENT'])
    # We have to do nrcolumns as the range function is counting from 0
    for x in range(1,nrcolumns_orig + 1):
      z = lpsolve('get_column', lp, x) # Column index
      # For some reason there is a double list..
      OBJECTIVE = (z[0])[0] # Column first element value
      colname = lpsolve('get_col_name', lp, x) # Column name
      # Not sure if the objective is 0.0 when there is none? But looks like it when tested on blend.mps only
      if OBJECTIVE == 0.0:
       #print("Element " + str(x) + " has no objective, value was: " + str(OBJECTIVE))
       pass
      else:
       # spamwriter.writerow([colname, OBJECTIVE])
       spamwriter.writerow([x, OBJECTIVE]) # HANA Proof Integers?

# P3 - VARIABLES
with open(target_directory + source_filename + '_IT_VARIABLE' + '.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write header
    spamwriter.writerow(["VARIABLEID","VARIABLENAME","TYPE","LOWERBOUND","UPPERBOUND"])
    for x in range(1,nrcolumns_orig + 1):
      z = lpsolve('get_column', lp, x) # Column index
      set = z[0]
      colname = lpsolve('get_col_name', lp, x) # Column name
      lowbo_orig = lpsolve('get_lowbo', lp, x) # Get lowerbound
      var_type = lpsolve('is_binary', lp, x) # Get variable type, needs to be checked though (int currently not handled)
      if var_type == 1:
        var_type = 'B'
      else:
        var_type = 'C'
      lowbo = format(lowbo_orig, 'f')
      if lowbo == '0.000000' or lowbo == '1000000000000000019884624838656.000000' or lowbo == '-1000000000000000019884624838656.000000':
        lowbo = ''
      upbo_orig = lpsolve('get_upbo', lp, x) # Get Upperbound
      upbo = format(upbo_orig, 'f')
      if upbo == '0.000000' or upbo == '1000000000000000019884624838656.000000' or upbo == '-1000000000000000019884624838656.000000':
        upbo = ''
      c = 'C'
      colnamecustom = ('C' + str(x))
      spamwriter.writerow([x, colname, var_type, lowbo , upbo])

# P4 - LINEARCONSTRAINTS
with open(target_directory + source_filename + '_IT_LINEARCONSTRAINTS' + '.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write header
    spamwriter.writerow(['CONSTRAINTID', 'CONSTRAINTNAME','TYPE','RHS'])
    for h in range(1,nrrows_orig + 1):
      rowname = lpsolve('get_row_name', lp, h) # Row name
      constr_type = lpsolve('get_constr_type', lp, h) # Row type 
      constr_value = lpsolve('get_rh', lp, h) # RHS
      if constr_type == 'LE':
        constr_type = 'L'
      elif constr_type == 'EQ':
        constr_type = 'E'
      elif constr_type == 'GE':
        constr_type = 'G'
      else:
        constr_type = 'ERROR'
      spamwriter.writerow([h, rowname, constr_type ,constr_value])

# P5 - LINEARCONSTRAINTMONOMES
with open(target_directory + source_filename + '_IT_LINEARCONSTRAINT_MONOMES' + '.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write header
    spamwriter.writerow(['CONSTRAINTID', 'VARIABLEID','COEFFICIENT'])
    for x in range(1,nrcolumns_orig + 1):
      for h in range(1,nrrows_orig + 1):
        COEFFICIENT = lpsolve('get_mat', lp, h, x)
        spamwriter.writerow([h, x, COEFFICIENT])

# Optional, solve the problem
print('### Writing done - Solving problem ###')
print(lpsolve('solve', lp ))
print('### Solving Done ###')

# Print Dimensions
print("# Rows (CONSTRAINTS): " + str(nrrows_orig) + " # Columns (VARIABLES): " + str(nrcolumns_orig) + " = Total records: " + str(nrcolumns_orig * nrrows_orig))