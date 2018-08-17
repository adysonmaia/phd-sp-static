/*********************************************
 * OPL 12.8.0.0 Model
 * Author: Adyson M. Maia
 * Creation Date: 30 juil. 2018 at 15:50:08
 *********************************************/

 /* Inputs */

int nbNodes = ...;
int nbApps = ...;
{string} Resources = ...;

range Nodes = 1..nbNodes;
range Apps = 1..nbApps;
string CPU = "CPU";
float eUpperLimit = 100000;
float queueMinDiff = 0.00001;
float distFactor = 0.001;

float nodeCapacity[Nodes][Resources] = ...;
float networkDelay[Nodes][Nodes] = ...;

tuple App {
    float deadline;
    int maxInstances;
    float requestRate; // lambda
    float workSize;
}
App apps[Apps] = ...;

int users[Apps][Nodes] = ...;
int nbUsers[a in Apps] = sum(h in Nodes) users[a][h];

// Linear function: k1 * x + k2
tuple LinearDemand {
    float k1;
    float k2;
}
LinearDemand resourceDemand[Apps][Resources] = ...;

float loadUpperLimit[a in Apps] = apps[a].requestRate * nbUsers[a];

/* Decision Variables */

dvar float e in 0..eUpperLimit;
dvar boolean place[Apps][Nodes]; // I
dvar boolean flowExists[Apps][Nodes][Nodes];
dvar float distribution[Apps][Nodes][Nodes] in 0..1; // alpha

dexpr float nodeLoad[a in Apps][h in Nodes] = sum(b in Nodes) distribution[a][b][h] * users[a][b] * apps[a].requestRate;
dvar float+ nodeLoadF[Apps][Nodes][Nodes];
dvar float+ nodeLoadE[Apps][Nodes];

/* Problem */

minimize e;
subject to {

  forall (a in Apps) {
    ctInstances: sum(h in Nodes) place[a][h] <= apps[a].maxInstances;
    ctInstances_2: sum(h in Nodes) place[a][h] >= 1;
  }  
   
  forall (a in Apps, b in Nodes, h in Nodes) {
    ctFlow: flowExists[a][b][h] <= place[a][h] * users[a][b];
  }    

  forall (a in Apps, b in Nodes) {
    ctDistribution: users[a][b] * sum(h in Nodes) distribution[a][b][h] == users[a][b];      
  }  
    	
  forall (a in Apps, b in Nodes, h in Nodes) {
    ctDistribution_2: distribution[a][b][h] <= flowExists[a][b][h];
    ctDistribution_3: distribution[a][b][h] >= flowExists[a][b][h] * distFactor;
  }
    
  forall (h in Nodes, r in Resources) {
    ctNodeCapacity: 
      sum(a in Apps) (nodeLoad[a][h] * resourceDemand[a][r].k1  + place[a][h] * resourceDemand[a][r].k2) 
      - nodeCapacity[h][r] <= 0;
  }        
    
  forall (a in Apps, h in Nodes) {
    ctQueue: 
      nodeLoad[a][h] * (resourceDemand[a][CPU].k1 - apps[a].workSize) 
      + place[a][h] * resourceDemand[a][CPU].k2 >= place[a][h] * queueMinDiff;     
  } 
        
  forall (a in Apps, b in Nodes, h in Nodes) {         
    ctDeadline:
      nodeLoadF[a][b][h] * networkDelay[b][h] * (resourceDemand[a][CPU].k1 - apps[a].workSize)
      + flowExists[a][b][h] * (resourceDemand[a][CPU].k2 * networkDelay[b][h] + apps[a].workSize)
      - nodeLoad[a][h] * apps[a].deadline * (resourceDemand[a][CPU].k1 - apps[a].workSize)
      - resourceDemand[a][CPU].k2 * apps[a].deadline
      - nodeLoadE[a][h] * (resourceDemand[a][CPU].k1 - apps[a].workSize)
      - e * resourceDemand[a][CPU].k2 <= 0;
   
    ctDeadline_f_1:
      nodeLoadF[a][b][h] >= loadUpperLimit[a] * (flowExists[a][b][h] -1) + nodeLoad[a][h];
    ctDeadline_f_2: nodeLoadF[a][b][h] <= flowExists[a][b][h] * loadUpperLimit[a];
    ctDeadline_f_3: nodeLoadF[a][b][h] <= nodeLoad[a][h];
  }         
    
  forall (a in Apps, h in Nodes) {
    ctDeadline_e_1: nodeLoadE[a][h] <= e * loadUpperLimit[a];
    ctDeadline_e_2: nodeLoadE[a][h] <= nodeLoad[a][h] * eUpperLimit;
    ctDeadline_e_3: 
      nodeLoadE[a][h] >= e * loadUpperLimit[a] + nodeLoad[a][h] * eUpperLimit 
      - loadUpperLimit[a] * eUpperLimit;
  }
}
 