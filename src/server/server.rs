use tonic::{transport::Server, Request, Response, Status};

use boid::boid_server::{Boid, BoidServer};
use boid::{Cord, BoidVec}, BoidRequest;

pub mod boid {
    tonic::include_proto!("boid");
}

#[derive(Default)]
pub struct BoidServer {}

#[tonic::async_trait]
impl Boid for BoidServer {
    async fn get_boid(
        &self,
        request: Request<BoidRequest>,
    ) -> Result<Response<BoidVec>, Status> {
        println!("Got a request from {:?}", request.remote_addr());

        let reply = boid::BoidVec {
            cords: BoidVec{Cord{1,2,3}},
        };
        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse().unwrap();
    let boid = BoidServer::default();

    println!("BoidServer listening on {}", addr);

    Server::builder()
        .add_service(BoidServer::new(boid))
        .serve(addr)
        .await?;

    Ok(())
}
