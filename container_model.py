import random
import shelve
import time
import uuid
import docker
import docker.errors as x
import hashlib

class PhpmyadminProvisioning:
    def __init__(self):
        #self.id = str(uuid.uuid1())
        self.dbports = shelve.open('dbports.db',writeback=True)
        self.userdb = shelve.open('users.db',writeback=True)
    def nomor_ports_belum_dialokasikan(self,no_port=11111):
        try:
            return (no_port in self.dbports.keys()) is False
        except:
            return True
    def find_port(self):
        the_port = 11111
        gagal=5
        while True:
            the_port = random.randint(11111, 22222)
            if (self.nomor_ports_belum_dialokasikan(the_port)):
                break
            time.sleep(1)
            gagal=gagal-1
            if (gagal<0):
                raise Exception
        #self.dbports[the_port]="1"
        return the_port

    def delete(self,username='default'):
        self.username=username
        try:
            docker_client = docker.DockerClient()

            container_mysql = docker_client.containers.get(f"{self.username}-mysql")
            container_mysql.stop()
            container_mysql.remove()

            container_phpmyadmin = docker_client.containers.get(f"{self.username}-phpmyadmin")
            container_phpmyadmin.stop()
            container_phpmyadmin.remove()

            network = docker_client.networks.get(f"{self.username}-networkbridge")
            network.remove()


            docker_client.containers.prune()
            docker_client.networks.prune()

            del self.userdb[f"{self.username}_mysql"]
            del self.userdb[f"{self.username}_mysql_port"]
            del self.userdb[f"{self.username}_mem_limit"]
            del self.userdb[f"{self.username}_phpmyadmin"]
            del self.userdb[f"{self.username}_phpmyadmin_port"]
            del self.userdb[f"{self.username}_networkbridge"]

            return dict(status="OK")
        except Exception as e:
            pass
    def get(self,username='default'):
        try:
            self.username = username
            info = dict(username=self.username,
                        phpmyadmin_port=self.userdb[f"{self.username}_phpmyadmin_port"],
                        mysql_port=self.userdb[f"{self.username}_mysql_port"])
            return dict(status="OK", info=info)
        except Exception as e:
            return dict(status="ERROR")

    def create(self,username='default', mem_limit="1g"):
        self.username=username
        self.mem_limit=mem_limit
        try:
            docker_client = docker.DockerClient()
            the_port_mysql = self.find_port()
            container_mysql = docker_client.containers.run(name=f"{self.username}-mysql", image="mysql:5.7", mem_limit=self.mem_limit,
                                                     environment=dict(MYSQL_USER=self.username,
                                                                      MYSQL_PASSWORD=f"{self.username}-6789",
                                                                      MYSQL_ROOT_PASSWORD="mysql-4567",
                                                                      MYSQL_DATABASE=f"{self.username}-db"), ports={'3306/tcp': the_port_mysql},
                                                     detach=True)
            the_port_phpmyadmin = self.find_port()
            container_phpmyadmin = docker_client.containers.run(name=f"{self.username}-phpmyadmin", image="phpmyadmin/phpmyadmin", mem_limit=self.mem_limit,
                                                     environment=dict(
                                                         PMA_HOST="mysql",
                                                         PMA_PORT="3306",
                                                         PMA_USER=self.username, PMA_PASSWORD=f"{self.username}-6789",
                                                         MYSQL_ROOT_PASSWORD="mysql-4567",
                                                         PMA_PMADB=f"{self.username}-db"), ports={'80/tcp': the_port_phpmyadmin},
                                                     detach=True)

            network =docker_client.networks.create(f"{self.username}-networkbridge",driver="bridge",check_duplicate=True)
            network.connect(container_mysql,aliases=["mysql"])
            network.connect(container_phpmyadmin,aliases=["phpmyadmin"])

            self.userdb[f"{self.username}_mysql"]=container_mysql.id
            self.userdb[f"{self.username}_mysql_port"]=the_port_mysql
            self.userdb[f"{self.username}_phpmyadmin"]=container_phpmyadmin.id
            self.userdb[f"{self.username}_phpmyadmin_port"]=the_port_phpmyadmin
            self.userdb[f"{self.username}_networkbridge"]=network.id
            self.userdb[f"{self.username}_mem_limit"]=self.mem_limit

            info = dict(username=self.username,
                        phpmyadmin_port=self.userdb[f"{self.username}_phpmyadmin_port"],
                        mysql_port=self.userdb[f"{self.username}_mysql_port"])
            return dict(status="OK",info=info)
        except Exception as e:
            return dict(status="ERROR")

    def get_stats(self,username):
        self.username=username
        docker_client = docker.APIClient()
        container_mysql = docker_client.containers(filters={'name':f"{self.username}-mysql"})
        container_pma = docker_client.containers(filters={'name':f"{self.username}-phpmyadmin"})
        mysql_stats = docker_client.stats(container_mysql[0]['Id'],stream=False)
        pma_stats = docker_client.stats(container_pma[0]['Id'],stream=False)
        mysql_info = dict(
            container_name=container_mysql[0]['Names'],
            state=container_mysql[0]['State'],
            status=container_mysql[0]['Status'],
            memory_stats=dict(
                usage=str(mysql_stats['memory_stats']['usage'])+" bytes",
                max_usage=str(mysql_stats['memory_stats']['max_usage'])+" bytes"
            )
        )
        pma_info = dict(
            container_name=container_pma[0]['Names'],
            state=container_pma[0]['State'],
            status=container_pma[0]['Status'],
            memory_stats=dict(
                usage=pma_stats['memory_stats']['usage'],
                max_usage=pma_stats['memory_stats']['max_usage']
            )
        )
        return dict(status="OK", MySQL=mysql_info, PHPMyAdmin=pma_info)


def run():
    c = PhpmyadminProvisioning()
    #create resource phpmyadmin-mysql
    # info = c.create(username='default')
    # print(info)

    #get resource info phpmyadmin-mysql
    # info = c.get(username='default')
    # c.delete(username='default')
    # docker_client = docker.from_env()
    # containers = docker_client.containers.list(filters={'name': 'mycluster-worker'})
    # print(docker_client.stats)


if __name__=='__main__':
    run()