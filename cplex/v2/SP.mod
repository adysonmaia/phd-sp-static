/*********************************************
 * OPL 12.8.0.0 Model
 * Author: adyson
 * Creation Date: 27/11/2018 at 16:06:38
 *********************************************/

int nbNodes = ...;
int nbApps = ...;
{string} Resources = ...;

range Nodes = 1..nbNodes;
range Apps = 1..nbApps;
string CPU = "CPU";
float queueMinDiff = 0.00001;

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

// Linear function: k1 * x + k2
tuple LinearDemand {
    float k1;
    float k2;
}
LinearDemand resourceDemand[Apps][Resources] = ...;

int requests[Apps][Nodes];
int loadUpperLimit[a in Apps] = 0;
execute {
	for (var a in Apps) {
		for (var b in Nodes) {
			requests[a][b] = Math.ceil(users[a][b] * apps[a].requestRate);
			loadUpperLimit[a] += requests[a][b] 
		}	
	}
}

/* Decision Variables */

dvar float+ e;
dvar boolean place[Apps][Nodes];
dvar int+ distribution[Apps][Nodes][Nodes];
dexpr int nodeLoad[a in Apps][h in Nodes] = sum(b in Nodes) distribution[a][b][h];
dvar int+ nodeLoadD[Apps][Nodes][Nodes];

/* Problem */

minimize e;
subject to {

  forall (a in Apps) {
    ctInstances: sum(h in Nodes) place[a][h] <= apps[a].maxInstances;
    ctInstances_2: sum(h in Nodes) place[a][h] >= 1;
  }  

  forall (a in Apps, b in Nodes) {
    ctDistribution: sum(h in Nodes) distribution[a][b][h] == requests[a][b];      
  }  
    	
  forall (a in Apps, b in Nodes, h in Nodes) {
    ctDistribution_2: distribution[a][b][h] <= place[a][h] * requests[a][b];
  }
    
  forall (h in Nodes, r in Resources) {
    ctNodeCapacity: 
      sum(a in Apps) (nodeLoad[a][h] * resourceDemand[a][r].k1  + place[a][h] * resourceDemand[a][r].k2) 
      <= nodeCapacity[h][r];
  }        
    
  forall (a in Apps, h in Nodes) {
    ctQueue: 
      nodeLoad[a][h] * (resourceDemand[a][CPU].k1 - apps[a].workSize) 
      + place[a][h] * resourceDemand[a][CPU].k2 >= place[a][h] * queueMinDiff;     
  } 
        
  forall (a in Apps, b in Nodes, h in Nodes) {         
    ctDeadline:
      nodeLoadD[a][b][h] * (resourceDemand[a][CPU].k1 - apps[a].workSize) * (networkDelay[b][h] - apps[a].deadline)
      + distribution[a][b][h] * (apps[a].workSize + resourceDemand[a][CPU].k1 * (networkDelay[b][h] - apps[a].deadline))
      <= e;
   
    ctDeadline_d_1:
      nodeLoadD[a][b][h] >= loadUpperLimit[a] * distribution[a][b][h] + requests[a][b] * nodeLoad[a][h] - loadUpperLimit[a] * requests[a][b];
    ctDeadline_d_2: nodeLoadD[a][b][h] <= loadUpperLimit[a] * distribution[a][b][h];
    ctDeadline_d_3: nodeLoadD[a][b][h] <= requests[a][b] * nodeLoad[a][h];
  }
}