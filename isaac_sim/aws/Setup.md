# Isaac Sim Setup

[Isaac Sim Github](https://github.com/isaac-sim/IsaacSim)

[AWS Deployment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_advanced_cloud_setup_aws.html)


_Set the Instance type to g6e.2xlarge. 
(Only the g6e.2xlarge instance type is supported.)_


Isaac Sim Version: 5.1

Instance Name: isaac-bot-control

Key pair name:    isaac-keys
Key pair options: ED25519 + .pem

---
## Connect to VM

1. Start AWS EC2 instance and get IPv4 assigned to it.

1. Connect:

   ```BASH
   ssh -i ~/.ssh/isaac-keys.pem  ubuntu@your-instance-public-ip
   ```

1. Set instance password. The needs to be set via SSH each time a new instance is created.

   ```BASH
   sudo passwd ubuntu
   ```

1. Check session running state says "console".

   ```BASH
   sudo dcv list-sessions
   ```

1. Install Windows NICE DCV client from https://www.amazondcv.com/

1. Open Amazon DCV Client and login using the username `ubuntu` and password just assigned.

1. Open shell on the instance and run Isaac Sim:

   ```BASH
   sudo chown -R ubuntu.root /opt/IsaacSim
   cd ~/IsaacSim && ./warmup.sh
   ./isaac-sim.sh
   ```

1. Copy file from local machine to aws instance:

   ```BASH
   scp -i ~/.ssh/isaac-keys.pem ~/setup_ur3_scene.py  ubuntu@63.179.210.157:/home/ubuntu
   ```

## Firewall Setup

1. Select: Create security group

1. Group Name: NVIDIA Isaac Sim

1. Description: NVIDIA Isaac Sim- Development Workstation (Linux)-2026.1.1-AutogenByAWSMP--1 created 2026-03-08T13:27:53.265Z

1. Rules

| Type       | Port  | Source | Description      |
|------------|-------|--------|------------------|
| SSH        |    22 | My IP  | For command-line |
| Custom TCP |  8443 | My IP  | CRITICAL: NICE DCV (The Isaac Sim GUI) |
| Custom TCP | 49100 | My IP  | WebRTC Streaming |
| Custom UDP | 47998 | My IP  | WebRTC Streaming |


## Request for vCPU Quota Increase

On launching the instance I am getting this error:

_You have requested more vCPU capacity than your current vCPU limit 
of 0 allows for the instance bucket that the specified instance type 
belongs to. Please visit http://aws.amazon.com/contact-us/ec2-request 
to request an adjustment to this limit._

_Quota increase requested for Running On-Demand G and VT instances. 
Check the 'Quota request history page' for Status and 
AWS Support Center Case (if created)._


1. Search for "Service Quotas" in the top search bar of the AWS Console.

2. On the left, click AWS services and search for Amazon Elastic Compute Cloud (EC2).

3. In the list of quotas, search for: "Running On-Demand G and VT instances"

4. Select that quota and click the Request increase at account level button. 
   We need at least 8 vCPUs. I recommend requesting 16.

5. Submit.


## Gemini AWS Price Estimates

| Instance Type | GPU Model          |  Approx. Hourly Cost,Best For             |
|---------------|--------------------|-------------------------------------------|
| g6e.2xlarge   | NVIDIA L40S (24GB) | ~$1.60 – $2.10,Standard Dev / Small Sims  |
| g6e.4xlarge   | NVIDIA L40S (24GB) | ~$2.50 – $3.20,Recommended for most users |
| g5.2xlarge    | NVIDIA A10G (24GB) | ~$1.20 – $1.50,Budget option (older gen)  |


* Storage: $40–$50 per month
* Data Transfer: Minimal unless you are streaming 4K video for 8 hours a day.
* To stop the hourly rate: Stop, don't Terminate and Auto-Shutdown



## NVIDIA Developers Program Membership

Use of the Isaac Sim workstation requires membership in the NVIDIA developers program, 
which developers can sign up for free at https://developer.nvidia.com . 

NVIDIA Isaac Sim is a free reference application built on NVIDIA Omniverse Kit. 
With a membership to the NVIDIA Developer Program, a free developer license is 
provided for Kit, which allows Isaac Sim to be freely used for non-production use.

