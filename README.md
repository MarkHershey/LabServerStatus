# LabServerStatus

## 3 Roles in the Architecture

-   **Self-Reporting Client**: The Client is installed on the Lab Workstation you would like to monitor. It is responsible for reporting its own status to the central Server.
-   **Server**: The Server is responsible for receiving the status reports from the Clients and managing the overall status of the Lab. It must be installed before the Clients and has a fixed IP address.
-   **ViewerClient (Web)**: The ViewerClient is responsible for displaying the status of the Lab to the user. It retrieves data from the Server via HTTP GET requests.

## Install Client on Lab Workstation

Step 0: Navigate to project root

```bash
git clone https://github.com/MarkHershey/LabServerStatus.git
cd LabServerStatus
```

Step 1: Create a runner script

-   Give current machine a unique name
    -   Modify [create-runner-script](create-runner-script) at [Line 53](https://github.com/MarkHershey/LabServerStatus/blob/285e56231934276a91110d59ccf00513d7ed5f08/create-runner-script#L53) and save the changes.
-   Run the script

    ```bash
    ./create-runner-script
    ```

Step 2: Setup a Cron job to run the runner script on system startup

-   Edit Cron job file

    ```bash
    sudo crontab -e
    ```

-   Add this line to the end of the file

    ```
    @reboot /bin/run_system_status_client &
    ```

Step 3: Reboot the system

```bash
sudo reboot
```

## Some Q & A

**Q: Why do we need a Client to be installed on each Linux machine that we want to monitor? How about using live SSH connections to replace the need of the self-reporting Clients?**

A: In this architecture, we assume that there are many data consumers who will use ViewerClients to consume the same data (the status of the lab workstation). We use a self-reporting paradigm to ensure that the least amount of overhead is created for the lab workstations. System status queries are performed periodically on the lab workstations and the data is reported to the central server at a fixed rate and negligible cost, regardless of the number of data consumers.

## TODOs

-   [ ] Add Client Payload Versioning
-   [ ] Create responses based on Machines Keys provided in the HTTP GET request
-   [ ] Create a Route to verify Bundle key and return a list of keys
-   [ ] Create a Route to verify Machine Keys
-   [ ] Improve Whitelist / Blacklist Management
-   [ ] Improve Constants Management
-   [ ] Improve Input Arguments Management
